#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/compose.staging.yml"
ENV_FILE="$PROJECT_DIR/.env.staging"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <GIT_SHA>"
    exit 1
fi

GIT_SHA="$1"
if [[ "$GIT_SHA" != sha-* ]]; then
    IMAGE_TAG="sha-${GIT_SHA}"
else
    IMAGE_TAG="$GIT_SHA"
fi

echo "Rolling back STAGING to $IMAGE_TAG"
cd "$PROJECT_DIR"

IMAGE_TAG="$IMAGE_TAG" docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d api

echo "Staging Rollback complete."