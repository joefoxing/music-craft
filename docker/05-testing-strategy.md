# Testing Strategy for Dockerized Production

> **Purpose**: Comprehensive testing approach before, during, and after migration.

## Table of Contents
1. [Local Testing](#local-testing)
2. [Staging/Parallel Testing](#stagingparallel-testing)
3. [Pre-Migration Validation](#pre-migration-validation)
4. [Production Smoke Tests](#production-smoke-tests)
5. [Automated CI Testing](#automated-ci-testing)

---

## Local Testing

### 1. Build Images Locally

```bash
# Build API image
docker build -f Dockerfile.api -t myapp/api:local-test .

# Build Web image  
docker build -f Dockerfile.web -t myapp/web:local-test .

# Verify images built
docker images | grep myapp
```

### 2. Test API Container in Isolation

```bash
# Create test environment file
cat > .env.test << EOF
DATABASE_URL=postgresql://user:pass@host.docker.internal:5432/testdb
SECRET_KEY=test-secret-key-for-local-only
LOG_LEVEL=DEBUG
EOF

# Run API container locally
docker run -d \
  --name api-test \
  --env-file .env.test \
  -p 8000:8000 \
  myapp/api:local-test

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:8000/health

# Check logs
docker logs api-test

# Cleanup
docker stop api-test && docker rm api-test
```

### 3. Test Full Stack Locally

```bash
# Copy example env and modify for local
cp .env.prod.example .env.local
cat >> .env.local << EOF
DOMAIN=localhost
IMAGE_TAG=local-test
EOF

# Edit DATABASE_URL to point to local/test database
# Edit other vars as needed

# Start stack
docker compose -f docker-compose.prod.yml --env-file .env.local up -d

# Verify all services
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl http://localhost/api/health
curl http://localhost/health  # or whatever your web health path is

# Stop
docker compose -f docker-compose.prod.yml down
```

---

## Staging/Parallel Testing

### 1. Deploy to Staging Server

```bash
# On staging server, use alternate ports or subdomain

# Option A: Different ports
cat > .env.staging << EOF
DOMAIN=staging.yourdomain.com
IMAGE_TAG=sha-ABC123
# ... other vars point to staging database
EOF

# Modify Caddyfile for staging (or use different Caddyfile)
docker compose -f docker-compose.prod.yml --env-file .env.staging up -d
```

### 2. Migration Dry Run

```bash
# Test migrations against staging database (copy of prod)
docker compose -f docker-compose.prod.yml --env-file .env.staging run --rm migrate

# Verify app works post-migration
curl https://staging.yourdomain.com/api/health
```

### 3. Load Testing

```bash
# Install k6 or use ab/curl for simple tests

# Concurrent request test
ab -n 1000 -c 10 https://staging.yourdomain.com/api/health

# Database connection test
for i in {1..50}; do
  curl -s https://staging.yourdomain.com/api/data &
done
wait

# Monitor connection count in Neon dashboard during test
```

---

## Pre-Migration Validation

### 1. Environment Validation Script

Create `scripts/validate-env.sh`:

```bash
#!/bin/bash
set -e

echo "=== Environment Validation ==="

# Check required files exist
[ -f .env.prod ] || { echo "ERROR: .env.prod missing"; exit 1; }
[ -f docker-compose.prod.yml ] || { echo "ERROR: docker-compose.prod.yml missing"; exit 1; }
[ -f Caddyfile ] || { echo "ERROR: Caddyfile missing"; exit 1; }

# Source env
set -a
source .env.prod
set +a

# Check required vars are set (not empty)
check_var() {
  local var_name=$1
  local var_value=${!var_name}
  if [ -z "$var_value" ]; then
    echo "ERROR: $var_name is not set"
    exit 1
  fi
  echo "OK: $var_name is set"
}

check_var "DOMAIN"
check_var "DATABASE_URL"
check_var "SECRET_KEY"
check_var "IMAGE_TAG"

# Validate DATABASE_URL format
if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
  echo "WARNING: DATABASE_URL doesn't start with postgresql://"
fi

# Validate DOMAIN doesn't include http/https
if [[ "$DOMAIN" =~ ^https?:// ]]; then
  echo "ERROR: DOMAIN should not include protocol (http/https)"
  exit 1
fi

# Check Docker is running
docker info > /dev/null || { echo "ERROR: Docker not running"; exit 1; }
echo "OK: Docker is running"

# Check ports are available
if ss -tlnp | grep -q ":80 "; then
  echo "WARNING: Port 80 is in use"
fi
if ss -tlnp | grep -q ":443 "; then
  echo "WARNING: Port 443 is in use"
fi

echo "=== All validations passed ==="
```

Run it:
```bash
chmod +x scripts/validate-env.sh
./scripts/validate-env.sh
```

### 2. Image Pull Test

```bash
# Test that the target image can be pulled
source .env.prod
FULL_IMAGE="${REGISTRY:-ghcr.io}/${REPO_OWNER}/${REPO_NAME}/api:${IMAGE_TAG}"

if docker pull "$FULL_IMAGE" 2>/dev/null; then
  echo "OK: Image pull successful"
else
  echo "ERROR: Cannot pull image $FULL_IMAGE"
  echo "Check: GitHub Actions completed, registry auth correct"
fi
```

### 3. Database Connectivity Test

```bash
# From within a test container
docker run --rm --env-file .env.prod myapp/api:local-test python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine('${DATABASE_URL}', echo=True)
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT version()'))
        print('Connected to:', result.scalar())

asyncio.run(test())
"
```

---

## Production Smoke Tests

### 1. Immediate Post-Deploy Tests

```bash
#!/bin/bash
# save as scripts/smoke-test.sh

DOMAIN="${DOMAIN:-yourdomain.com}"
TIMEOUT=10

echo "=== Smoke Tests for $DOMAIN ==="

# Test 1: Health endpoint
echo -n "Health check... "
if curl -sf --max-time $TIMEOUT "https://$DOMAIN/health" > /dev/null; then
  echo "OK"
else
  echo "FAILED"
  exit 1
fi

# Test 2: API health
echo -n "API health... "
if curl -sf --max-time $TIMEOUT "https://$DOMAIN/api/health" > /dev/null; then
  echo "OK"
else
  echo "FAILED"
  exit 1
fi

# Test 3: Homepage loads
echo -n "Homepage... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time $TIMEOUT "https://$DOMAIN/")
if [ "$HTTP_CODE" == "200" ]; then
  echo "OK"
else
  echo "FAILED (HTTP $HTTP_CODE)"
  exit 1
fi

# Test 4: HTTPS certificate valid
echo -n "TLS certificate... "
if echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -checkend 0 > /dev/null; then
  echo "OK"
else
  echo "FAILED (cert expired or invalid)"
  exit 1
fi

# Test 5: Response time < 1s
echo -n "Response time... "
RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" "https://$DOMAIN/health")
if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
  echo "OK (${RESPONSE_TIME}s)"
else
  echo "SLOW (${RESPONSE_TIME}s)"
fi

echo "=== All smoke tests passed ==="
```

### 2. End-to-End User Flow Tests

```bash
# Using curl to simulate user actions

BASE_URL="https://yourdomain.com"
COOKIE_JAR=$(mktemp)

# 1. Register test user
curl -s -c "$COOKIE_JAR" -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# 2. Login
curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123"}'

# 3. Create resource
curl -s -b "$COOKIE_JAR" -X POST "$BASE_URL/api/items" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item"}'

# 4. List resources
curl -s -b "$COOKIE_JAR" "$BASE_URL/api/items"

# 5. Logout
curl -s -b "$COOKIE_JAR" -X POST "$BASE_URL/api/auth/logout"

# Cleanup
rm "$COOKIE_JAR"
```

### 3. Log Validation

```bash
# Check for errors in logs (run 5 minutes after deploy)
docker compose -f docker-compose.prod.yml logs --since=5m | grep -E "(ERROR|CRITICAL|Traceback)" || echo "No errors found"

# Check warning patterns
docker compose -f docker-compose.prod.yml logs --since=5m | grep -E "(WARNING|WARN)" | head -20
```

---

## Automated CI Testing

### 1. Add to GitHub Actions Workflow

Add this job to `.github/workflows/deploy.yml`:

```yaml
  integration-test:
    runs-on: ubuntu-latest
    needs: build
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      
      - name: Run API tests in container
        run: |
          docker run --rm \
            --network host \
            -e DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test \
            -e SECRET_KEY=test-secret \
            ${{ needs.build.outputs.api_image }} \
            pytest tests/ -v --tb=short

      - name: Test container starts and health check responds
        run: |
          docker run -d --name api-test \
            --network host \
            -e DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test \
            -e SECRET_KEY=test-secret \
            -p 8000:8000 \
            ${{ needs.build.outputs.api_image }}
          
          # Wait for startup
          sleep 10
          
          # Test health
          curl -f http://localhost:8000/health || exit 1
          
          docker stop api-test && docker rm api-test
```

### 2. Dockerfile Linting

```yaml
  lint-dockerfile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile.api
          
      - uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: Dockerfile.web
```

### 3. Security Scanning

```yaml
  security-scan:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ needs.build.outputs.api_image }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

---

## Testing Checklist

### Before Migration
- [ ] Images build successfully locally
- [ ] Containers pass health checks locally
- [ ] Full stack runs locally with `docker compose`
- [ ] Staging deployment successful
- [ ] Migrations tested on staging database
- [ ] Load test passed (no connection exhaustion)
- [ ] Environment validation script passes
- [ ] Image pull test from production server works

### During Migration
- [ ] Smoke tests pass immediately after deploy
- [ ] No ERROR logs in first 5 minutes
- [ ] Response times < 1 second
- [ ] TLS certificate valid
- [ ] Database connections within limits

### After Migration (24 hours)
- [ ] No memory leaks (usage stable)
- [ ] Log rotation working
- [ ] Background jobs processing (if applicable)
- [ ] File uploads working (if applicable)
- [ ] Email sending working (if applicable)
- [ ] Can successfully rollback if needed

---

## Debugging Failed Tests

### Container Won't Start
```bash
# Check logs
docker compose logs <service-name>

# Check exit code
docker inspect <container-id> --format='{{.State.ExitCode}}'

# Run with interactive shell to debug
docker run --rm -it --entrypoint sh myapp/api:local-test
```

### Health Check Failing
```bash
# Test manually from inside container
docker exec -it <container-id> sh
wget --spider http://localhost:8000/health

# Check if service is actually listening
netstat -tlnp | grep 8000
```

### Database Connection Issues
```bash
# Test connectivity from container
docker run --rm --env-file .env.prod myapp/api:local-test python -c "
import psycopg2
conn = psycopg2.connect('${DATABASE_URL}')
print('Connected!')
conn.close()
"

# Check if SSL is required (Neon usually requires it)
```

### Port Conflicts
```bash
# Find what's using port 80
sudo ss -tlnp | grep :80
sudo lsof -i :80

# Kill process or change Docker port mapping
```

---

## Quick Reference Commands

```bash
# Full local test cycle
docker compose -f docker-compose.prod.yml --env-file .env.local down -v \
  && docker compose -f docker-compose.prod.yml --env-file .env.local up -d --build \
  && sleep 10 \
  && curl http://localhost/api/health \
  && docker compose logs -f

# Inspect failing container
docker exec -it <container-id> sh
docker inspect <container-id> --format='{{json .State}}' | jq

# Force recreate
docker compose up -d --force-recreate --no-deps api

# View resource usage
docker stats --no-stream
```
