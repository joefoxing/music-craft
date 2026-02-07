#!/bin/bash
set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.prod"
LOCK_FILE="/tmp/app-deploy.lock"
HEALTH_TIMEOUT=120
ROLLBACK_TAG_FILE="$PROJECT_DIR/.rollback-tag"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
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

log_info "Starting PROD deployment: $IMAGE_TAG"
cd "$PROJECT_DIR"

if [ ! -f "$ENV_FILE" ]; then
    log_error "$ENV_FILE not found"
    exit 1
fi

source "$ENV_FILE"

# Record current version
CURRENT_TAG=$(docker compose -f "$COMPOSE_FILE" ps -q api 2>/dev/null | xargs -I {} docker inspect --format='{{.Config.Image}}' {} 2>/dev/null | grep -o 'sha-[a-f0-9]*' || echo "unknown")
if [ "$CURRENT_TAG" != "unknown" ]; then
    echo "$CURRENT_TAG" > "$ROLLBACK_TAG_FILE"
fi

# Pull
log_info "Pulling $IMAGE_TAG..."
IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull api

# Migrate
log_info "Running migrations..."
IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm migrate

# Deploy
log_info "Updating services..."
# We update 'api' and ensure 'proxy' is running. Proxy recreates only if config changed.
IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d api proxy

# Healthcheck
log_info "Waiting for health..."
START_TIME=$(date +%s)
while true; do
    API_HEALTH=$(docker compose -f "$COMPOSE_FILE" ps -q api | xargs -I {} docker inspect --format='{{.State.Health.Status}}' {} 2>/dev/null || echo "unhealthy")
    if [ "$API_HEALTH" == "healthy" ]; then
        log_info "API healthy!"
        break
    fi
    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $ELAPSED -ge $HEALTH_TIMEOUT ]; then
        log_error "Timeout. Rolling back..."
        if [ -f "$ROLLBACK_TAG_FILE" ]; then
            "$SCRIPT_DIR/rollback.sh" "$(cat "$ROLLBACK_TAG_FILE")"
        fi
        exit 1
    fi
    sleep 5
done

# External verification
DOMAIN=${DOMAIN:-joefoxing.com}
curl -sf "https://$DOMAIN/health" >/dev/null && log_info "External health check passed" || log_warn "External health check failed"

log_info "Deployment Success: $IMAGE_TAG"