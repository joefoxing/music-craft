# Production & Staging Runbook (Docker + Caddy)

## Overview
This setup runs **Production** (`joefoxing.com`) and **Staging** (`staging.joefoxing.com`) concurrently on the same VPS using Docker Compose.

- **Ingress:** A single Caddy instance (in the Production stack) binds ports 80/443.
- **Routing:** Caddy routes traffic to `prod_app` or `staging_app` via a shared external network `proxy_net`.
- **Isolation:** Staging and Prod have separate databases, secrets, and container lifecycles.

## 1. First-Time Setup

### A. Server Prep
Ensure Docker and Docker Compose are installed.

```bash
# Create the shared network
docker network create proxy_net || true
```

### B. Repository Setup
```bash
# As deploy user
cd ~
mkdir app
cd app
git clone https://github.com/joefoxing/lyric_cover_staging.git .
# OR if already cloned, just pull
git pull origin main
```

**Note:** If migrating from root to deploy user, see `MIGRATE_TO_DEPLOY_USER.md` for detailed migration steps.

### C. Environment Variables
Create the secret configuration files as the `deploy` user.

**Production:**
```bash
# As deploy user
cp .env.prod.example .env.prod
nano .env.prod
# Set APP_ENV=production
# Set DATABASE_URL=... (Production DB)
# Set SECRET_KEY=...

# Secure permissions
chmod 600 .env.prod
```

**Staging:**
```bash
# As deploy user
cp .env.staging.example .env.staging
nano .env.staging
# Set APP_ENV=staging
# Set DATABASE_URL=... (Staging DB)
# Set SECRET_KEY=...

# Secure permissions
chmod 600 .env.staging
```

## 2. Deployment

### A. Deploy Staging
This pulls the latest code/images for staging, runs migrations against the staging DB, and restarts the staging API. **Production is not affected.**

```bash
# As deploy user, manual run (uses scripts/deploy-staging.sh)
# Replace SHA with the git commit hash you want to deploy
cd ~/app
./scripts/deploy-staging.sh sha-3eaad254a2c4
```

**What it does:**
1.  Pulls `api` image for the SHA.
2.  Runs `alembic upgrade head` using `.env.staging`.
3.  Updates `app_staging` service.

### B. Deploy Production
This updates the production application and the Caddy proxy.

```bash
# As deploy user, manual run (uses scripts/deploy.sh)
cd ~/app
./scripts/deploy.sh sha-3eaad254a2c4
```

**What it does:**
1.  Pulls `api` image for the SHA.
2.  Runs `alembic upgrade head` using `.env.prod`.
3.  Updates `app_prod` service (and `proxy` if config changed).

## 3. Operations & Monitoring

### View Logs

**Production:**
```bash
# As deploy user
cd ~/app

# App logs
docker compose -f compose.prod.yml logs -f api

# Caddy logs
docker compose -f compose.prod.yml logs -f proxy
```

**Staging:**
```bash
# As deploy user
cd ~/app
docker compose -f compose.staging.yml logs -f api
```

### Check Status
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
Expected output:
- `caddy`: Up, 0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
- `prod_app` (or similar): Up, 8000/tcp
- `staging_app` (or similar): Up, 8000/tcp

### Health Checks
```bash
curl -I https://joefoxing.com/health
curl -I https://staging.joefoxing.com/health
```

## 4. Rollback

If a deployment fails, use the rollback scripts to revert to the previous (or specific) version.

**Staging Rollback:**
```bash
# As deploy user
cd ~/app

# Rollback to previous version (automatically recorded)
./scripts/rollback-staging.sh

# OR rollback to specific SHA
./scripts/rollback-staging.sh <OLD_SHA>
```

**Production Rollback:**
```bash
# As deploy user
cd ~/app

# Rollback to previous version
./scripts/rollback.sh

# OR rollback to specific SHA
./scripts/rollback.sh <OLD_SHA>
```

## 5. Troubleshooting

**"Bad Gateway" (502):**
- Check if the app container is running: `docker ps`.
- Check app logs: `docker compose -f compose.prod.yml logs api`.
- Check if Caddy can reach the app: `docker exec -it caddy curl http://prod_app:8000/health`.

**"Staging not reachable":**
- Ensure `staging_app` is on `proxy_net`: `docker inspect staging_app`.
- Ensure Caddy configuration is reloaded (usually happens on prod deploy, or force restart Caddy: `docker compose -f compose.prod.yml restart proxy`).
