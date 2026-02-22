#!/bin/bash
set -e

# Start postgres using the official entrypoint in background
docker-entrypoint.sh postgres &
PG_PID=$!

# Wait until postgres accepts LOCAL socket connections (not just pg_isready which
# can return true before auth is fully initialised on a reused volume).
MAX_WAIT=60
WAITED=0
until psql -U "${POSTGRES_USER:-postgres}" -c 'SELECT 1' > /dev/null 2>&1; do
    sleep 1
    WAITED=$((WAITED + 1))
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo "ERROR: Timed out waiting for postgres to be ready" >&2
        exit 1
    fi
done

# Always sync the password from the env var — fixes "password auth failed"
# after volume reuse (POSTGRES_PASSWORD is only applied on first init otherwise)
psql -U "${POSTGRES_USER:-postgres}" -c \
  "ALTER USER ${POSTGRES_USER:-postgres} WITH PASSWORD '${POSTGRES_PASSWORD:-postgres}';" \
  > /dev/null 2>&1

echo "[entrypoint] Password synced for user ${POSTGRES_USER:-postgres}"

# Hand off to the background postgres process
wait "$PG_PID"
