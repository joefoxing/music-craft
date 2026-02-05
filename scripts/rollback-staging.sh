#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# STAGING ROLLBACK SCRIPT
#
# Usage:
#   ./scripts/rollback-staging.sh [TARGET_SHA]
#
# If TARGET_SHA is not provided, rolls back to the previous version
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BASE_COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
STAGING_COMPOSE_FILE="$PROJECT_DIR/compose.staging.yml"
ENV_FILE="$PROJECT_DIR/.env.staging"
ROLLBACK_TAG_FILE="$PROJECT_DIR/.rollback-tag-staging"
PROJECT_NAME="app-staging"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[STAGING-ROLLBACK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[STAGING-ROLLBACK]${NC} $1"; }
log_error() { echo -e "${RED}[STAGING-ROLLBACK]${NC} $1"; }

# Determine target SHA
if [ $# -eq 1 ]; then
    TARGET_SHA="$1"
    log_info "Rolling back to specified SHA: $TARGET_SHA"
elif [ -f "$ROLLBACK_TAG_FILE" ]; then
    TARGET_SHA=$(cat "$ROLLBACK_TAG_FILE")
    log_info "Rolling back to previous version: $TARGET_SHA"
else
    log_error "No rollback target specified and no previous version found"
    log_error "Usage: $0 [TARGET_SHA]"
    exit 1
fi

# Validate SHA format
if [[ ! "$TARGET_SHA" =~ ^sha-[a-f0-9]+$ ]]; then
    log_error "Invalid SHA format: $TARGET_SHA"
    log_error "Expected format: sha-abc123def456"
    exit 1
fi

cd "$PROJECT_DIR"

# Load environment
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file not found: $ENV_FILE"
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

log_warn "═══════════════════════════════════════════════════════════"
log_warn "ROLLING BACK STAGING ENVIRONMENT"
log_warn "Target version: $TARGET_SHA"
log_warn "═══════════════════════════════════════════════════════════"

# Pull target images
log_info "Pulling rollback images..."
IMAGE_TAG="$TARGET_SHA" docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" --env-file "$ENV_FILE" pull

# Deploy rollback version
log_info "Deploying rollback version..."
IMAGE_TAG="$TARGET_SHA" docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps api

# Wait for health
log_info "Waiting for API to become healthy..."
for i in {1..30}; do
    API_HEALTH=$(docker compose -p "$PROJECT_NAME" -f "$BASE_COMPOSE_FILE" -f "$STAGING_COMPOSE_FILE" ps -q api | xargs -I {} docker inspect --format='{{.State.Health.Status}}' {} 2>/dev/null || echo "unhealthy")
    
    if [ "$API_HEALTH" == "healthy" ]; then
        log_info "Rollback successful! API is healthy."
        log_info "Rolled back to: $TARGET_SHA"
        exit 0
    fi
    
    echo "Waiting... API: $API_HEALTH ($i/30)"
    sleep 5
done

log_error "Rollback health checks failed!"
log_error "Manual intervention required"
exit 1
