#!/bin/bash
set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/compose.staging.yml"
ENV_FILE="$PROJECT_DIR/.env.staging"
LOCK_FILE="/tmp/app-staging-deploy.lock"
HEALTH_TIMEOUT=120
DEPLOY_SHA_FILE="$PROJECT_DIR/DEPLOYED_SHA_STAGING.txt"
DEPLOY_SHA_PREV_FILE="$PROJECT_DIR/DEPLOYED_SHA_STAGING.txt.prev"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[STAGING]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

cleanup() { rm -f "$LOCK_FILE"; }
trap cleanup EXIT

if [ $# -ne 1 ]; then
    log_error "Usage: $0 <GIT_SHA>"
    exit 1
fi

GIT_SHA="$1"
IMAGE_TAG="sha-${GIT_SHA}"

exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    log_error "Deployment in progress. Exiting."
    exit 1
fi

log_info "Starting STAGING deployment: $IMAGE_TAG"
cd "$PROJECT_DIR"

if [ ! -f "$ENV_FILE" ]; then
    log_error "$ENV_FILE not found"
    exit 1
fi

source "$ENV_FILE"

# Version Tracking: Shift current -> prev
if [ -f "$DEPLOY_SHA_FILE" ]; then
    cp "$DEPLOY_SHA_FILE" "$DEPLOY_SHA_PREV_FILE"
fi

# Pull
log_info "Pulling..."
IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull api

# Deploy
log_info "Updating staging api..."
# Only 'api' exists in staging compose now
IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --remove-orphans api

# Healthcheck
log_info "Waiting for health..."
START_TIME=$(date +%s)
while true; do
    API_HEALTH=$(IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps -q api | xargs -I {} docker inspect --format='{{.State.Health.Status}}' {} 2>/dev/null || echo "unhealthy")
    if [ "$API_HEALTH" == "healthy" ]; then
        log_info "API healthy!"
        # Update current version file on success
        echo "$GIT_SHA" > "$DEPLOY_SHA_FILE"
        break
    fi
    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
        log_error "Timeout. Rolling back..."
        
        # Debug: Show logs before rollback
        log_warn "--- CONTAINER LOGS ---"
        IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs api || true
        log_warn "--- CONTAINER INSPECT ---"
        IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps api || true
        log_warn "----------------------"

        if [ -f "$DEPLOY_SHA_PREV_FILE" ]; then
            PREV_SHA=$(cat "$DEPLOY_SHA_PREV_FILE")
            log_warn "Rolling back to $PREV_SHA"
            "$SCRIPT_DIR/rollback-staging.sh" "$PREV_SHA"
        fi
        exit 1
    fi
    sleep 5
done

# External verification
DOMAIN=${DOMAIN:-staging.joefoxing.com}
curl -sf "https://$DOMAIN/health" >/dev/null && log_info "External health check passed" || log_warn "External health check failed"

log_info "Staging Deployment Success: $IMAGE_TAG"
