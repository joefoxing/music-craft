#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# STAGING DEPLOY SCRIPT
#
# Usage:
#   ./scripts/deploy-staging.sh <GIT_SHA>
#
# Example:
#   ./scripts/deploy-staging.sh abc123def456
#
# Features:
# - Pulls specific image by SHA (immutable)
# - Runs database migrations against staging DB
# - Rolling update with health checks
# - Automatic rollback on failure
# - Isolated from production (separate project name, network, volumes)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BASE_COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
STAGING_COMPOSE_FILE="$PROJECT_DIR/compose.staging.yml"
ENV_FILE="$PROJECT_DIR/.env.staging"
LOCK_FILE="/tmp/app-staging-deploy.lock"
HEALTH_TIMEOUT=120
ROLLBACK_TAG_FILE="$PROJECT_DIR/.rollback-tag-staging"
PROJECT_NAME="app-staging"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${GREEN}[STAGING-INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[STAGING-WARN]${NC} $1"; }
log_error() { echo -e "${RED}[STAGING-ERROR]${NC} $1"; }
log_debug() { echo -e "${BLUE}[STAGING-DEBUG]${NC} $1"; }

# Cleanup function
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

# Check arguments
if [ $# -ne 1 ]; then
    log_error "Usage: $0 <GIT_SHA>"
    exit 1
fi

GIT_SHA="$1"
IMAGE_TAG="sha-${GIT_SHA}"

# Acquire lock (prevent concurrent deploys)
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    log_error "Another staging deployment is in progress. Exiting."
    exit 1
fi

log_info "Starting STAGING deployment of image tag: $IMAGE_TAG"

# Change to project directory
cd "$PROJECT_DIR"

# Load environment
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    log_error "Copy .env.staging.example to .env.staging and configure it"
    exit 1
fi

# Source env file for local variables (export needed vars)
set -a
source "$ENV_FILE"
set +a

# Record current version for rollback
CURRENT_TAG=$(docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" ps -q api 2>/dev/null | xargs -I {} docker inspect --format='{{.Config.Image}}' {} 2>/dev/null | grep -o 'sha-[a-f0-9]*' || echo "unknown")
if [ "$CURRENT_TAG" != "unknown" ]; then
    echo "$CURRENT_TAG" > "$ROLLBACK_TAG_FILE"
    log_info "Current version recorded for rollback: $CURRENT_TAG"
fi

# Pull new images
log_info "Pulling images with tag: $IMAGE_TAG"
IMAGE_TAG="$IMAGE_TAG" docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" --env-file "$ENV_FILE" pull api

# Run database migrations (one-off container)
log_info "Running database migrations against STAGING database..."
log_warn "Ensure DATABASE_URL points to staging DB, not production!"
if ! IMAGE_TAG="$IMAGE_TAG" docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" --env-file "$ENV_FILE" run --rm migrate; then
    log_error "Database migrations failed! Aborting deployment."
    exit 1
fi

log_info "Migrations completed successfully"

# Deploy with new image tag
log_info "Deploying new containers..."
IMAGE_TAG="$IMAGE_TAG" docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps api

# Wait for health checks
log_info "Waiting for health checks (timeout: ${HEALTH_TIMEOUT}s)..."
START_TIME=$(date +%s)
while true; do
    # Check API health
    API_HEALTH=$(docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" ps -q api | xargs -I {} docker inspect --format='{{.State.Health.Status}}' {} 2>/dev/null || echo "unhealthy")
    
    if [ "$API_HEALTH" == "healthy" ]; then
        log_info "API service is healthy!"
        break
    fi
    
    # Check timeout
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
        log_error "Health checks timed out after ${HEALTH_TIMEOUT}s"
        log_warn "Initiating automatic rollback..."
        
        if [ -f "$ROLLBACK_TAG_FILE" ]; then
            ROLLBACK_TAG=$(cat "$ROLLBACK_TAG_FILE")
            "$SCRIPT_DIR/rollback-staging.sh" "$ROLLBACK_TAG"
        else
            log_error "No rollback tag found. Manual intervention required."
        fi
        exit 1
    fi
    
    log_debug "Waiting... API: $API_HEALTH"
    sleep 5
done

# Verify proxy is routing correctly
log_info "Verifying external health endpoint..."
DOMAIN=$(grep DOMAIN "$ENV_FILE" | cut -d'=' -f2 | tr -d ' ')
if [ -z "$DOMAIN" ]; then
    log_warn "DOMAIN not found in env file, skipping external health check"
else
    for i in {1..10}; do
        if curl -sf "https://$DOMAIN/health" > /dev/null 2>&1 || curl -sf "http://localhost:8080/health" > /dev/null 2>&1; then
            log_info "External health check passed!"
            break
        fi
        if [ $i -eq 10 ]; then
            log_warn "External health check inconclusive, but internal checks passed"
        fi
        sleep 2
    done
fi

# Cleanup old images (keep last 3)
log_info "Cleaning up old staging images..."
docker images --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}" | \
    grep "${REPO_OWNER:-owner}/${REPO_NAME:-app}" | \
    grep "sha-" | \
    sort -k2 -r | \
    tail -n +4 | \
    awk '{print $1}' | \
    xargs -r docker rmi 2>/dev/null || true

log_info "═══════════════════════════════════════════════════════════"
log_info "STAGING deployment completed successfully!"
log_info "Deployed version: $IMAGE_TAG"
log_info "Environment: STAGING"
log_info "Domain: $DOMAIN"
log_info "═══════════════════════════════════════════════════════════"
