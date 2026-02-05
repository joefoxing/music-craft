#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ROLLBACK SCRIPT
#
# Usage:
#   ./scripts/rollback.sh [GIT_SHA]
#
# Examples:
#   ./scripts/rollback.sh abc123def456  # Rollback to specific SHA
#   ./scripts/rollback.sh               # Rollback to previous version (from .rollback-tag)
#
# Features:
# - Quick rollback to known good version
# - Validates image exists before rolling back
# - Maintains database compatibility (rollback does NOT revert migrations)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.prod"
LOCK_FILE="/tmp/app-deploy.lock"
ROLLBACK_TAG_FILE="$PROJECT_DIR/.rollback-tag"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_prompt() { echo -e "${BLUE}[PROMPT]${NC} $1"; }

# Cleanup
cleanup() { rm -f "$LOCK_FILE"; }
trap cleanup EXIT

# Acquire lock
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    log_error "Another deployment/rollback is in progress. Exiting."
    exit 1
fi

# Determine rollback target
if [ $# -eq 1 ]; then
    TARGET_TAG="sha-$1"
    log_info "Rolling back to specified version: $TARGET_TAG"
elif [ -f "$ROLLBACK_TAG_FILE" ]; then
    TARGET_TAG=$(cat "$ROLLBACK_TAG_FILE")
    log_info "Rolling back to previous version: $TARGET_TAG"
else
    log_error "No rollback target specified and no previous version recorded."
    log_error "Usage: $0 <GIT_SHA>"
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

# Get current version for confirmation
CURRENT_TAG=$(docker compose -f "$COMPOSE_FILE" ps -q api 2>/dev/null | xargs -I {} docker inspect --format='{{.Config.Image}}' {} 2>/dev/null | grep -o 'sha-[a-f0-9]*' || echo "unknown")

log_warn "=========================================="
log_warn "ROLLBACK OPERATION"
log_warn "=========================================="
log_warn "Current version: $CURRENT_TAG"
log_warn "Target version:  $TARGET_TAG"
log_warn ""
log_warn "IMPORTANT: This will NOT revert database migrations."
log_warn "Ensure the target code is compatible with current schema."
log_warn "=========================================="

read -p "Are you sure you want to rollback? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log_info "Rollback cancelled."
    exit 0
fi

# Check if image exists locally or can be pulled
log_info "Checking for image: $TARGET_TAG"
FULL_IMAGE="${REGISTRY:-ghcr.io}/${REPO_OWNER:-owner}/${REPO_NAME:-app}/api:${TARGET_TAG}"

if ! docker pull "$FULL_IMAGE" 2>/dev/null; then
    log_error "Failed to pull image: $FULL_IMAGE"
    log_error "Rollback target may not exist in registry."
    exit 1
fi

# Record current for potential "roll-forward"
echo "$CURRENT_TAG" > "$ROLLBACK_TAG_FILE"

# Perform rollback
log_info "Stopping current containers..."
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop api web worker

log_info "Starting rollback version..."
IMAGE_TAG="$TARGET_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d api web worker

# Wait for health
log_info "Waiting for services to become healthy..."
for i in {1..30}; do
    API_HEALTH=$(docker compose -f "$COMPOSE_FILE" ps -q api | xargs -I {} docker inspect --format='{{.State.Health.Status}}' {} 2>/dev/null || echo "unhealthy")
    if [ "$API_HEALTH" == "healthy" ]; then
        log_info "Rollback successful! API is healthy."
        log_info "Rolled back to: $TARGET_TAG"
        exit 0
    fi
    sleep 2
done

log_error "Rollback completed but health checks failed!"
log_error "Manual intervention may be required."
exit 1
