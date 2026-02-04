# Staging Environment Setup Guide

Complete guide for deploying and managing the isolated staging environment.

## Overview

Staging is a **fully isolated environment** that mirrors production but uses separate:
- **Domain**: `staging.joefoxing.com`
- **Database**: Separate Neon database/project
- **Containers**: Isolated Docker Compose project (`app-staging`)
- **Network**: Separate Docker network (172.21.0.0/16)
- **Secrets**: Different credentials from production
- **Deploy trigger**: `develop` branch → staging, `main` branch → production

---

## 1. Infrastructure Setup

### A. DNS Configuration
Add DNS A record pointing to your VPS:
```
staging.joefoxing.com → <VPS_IP>
```

### B. Neon Database Setup
1. Create a **new Neon project** or database for staging
2. Generate separate credentials (user/password)
3. Note the connection string (will be used in `.env.staging`)
4. **CRITICAL**: Never use production database credentials in staging

### C. GitHub Environments & Secrets

#### Create GitHub Environment: `staging`
In your GitHub repo: **Settings → Environments → New environment**

Name: `staging`

#### Add Environment Variables (staging):
```
STAGING_DOMAIN=staging.joefoxing.com
STAGING_HOST=<your-vps-ip-or-hostname>
STAGING_USER=<ssh-user>
```

#### Add Environment Secrets (staging):
- Same `SSH_PRIVATE_KEY` as production (or separate if using different server)

#### Update Production Environment Variables:
Ensure `production` environment has:
```
DOMAIN=joefoxing.com
PROD_HOST=<your-vps-ip-or-hostname>
PROD_USER=<ssh-user>
```

---

## 2. Server Setup (VPS)

### A. Create Staging Directory
```bash
ssh user@your-vps
mkdir -p ~/app
cd ~/app
```

### B. Clone Repository
```bash
git clone <your-repo-url> .
git checkout develop
```

### C. Create `.env.staging` File
```bash
cp .env.staging.example .env.staging
nano .env.staging
```

**Fill in all required values:**
```bash
# CRITICAL: Use DIFFERENT values from production
IMAGE_TAG=sha-<initial-commit>
REGISTRY=ghcr.io
REPO_OWNER=<your-github-username>
REPO_NAME=<your-repo-name>

DOMAIN=staging.joefoxing.com
APP_ENV=staging
LOG_LEVEL=DEBUG

# SEPARATE Neon database
DATABASE_URL=postgresql://user:password@staging-host/staging_db?sslmode=require

# DIFFERENT secrets (generate new ones)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)

# Separate S3 bucket or prefix
S3_BUCKET=yourapp-staging

# Test/sandbox API keys
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### D. Make Scripts Executable
```bash
chmod +x scripts/deploy-staging.sh
chmod +x scripts/rollback-staging.sh
chmod +x scripts/deploy.sh
chmod +x scripts/rollback.sh
```

### E. Login to GitHub Container Registry
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u <your-username> --password-stdin
```

---

## 3. Deployment Workflow

### Branch-Based Deployments

#### Staging Deployment (Automatic)
```bash
# Push to develop branch
git checkout develop
git add .
git commit -m "Feature: new functionality"
git push origin develop
```

**What happens:**
1. GitHub Actions builds Docker images tagged with git SHA
2. Pushes images to `ghcr.io`
3. Runs tests
4. Deploys to staging environment
5. Runs health checks

#### Production Deployment (Automatic)
```bash
# Merge to main branch
git checkout main
git merge develop
git push origin main
```

**What happens:**
1. Same build process (reuses images if SHA matches)
2. Deploys to production environment
3. Runs health checks

### Manual Deployment (SSH)

#### Deploy Staging Manually
```bash
ssh user@vps
cd ~/app
git pull origin develop
./scripts/deploy-staging.sh <git-sha>
```

#### Deploy Production Manually
```bash
ssh user@vps
cd ~/app
git pull origin main
./scripts/deploy.sh <git-sha>
```

---

## 4. Container Management

### View Staging Containers
```bash
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml ps
```

### View Staging Logs
```bash
# All services
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml logs -f

# Specific service
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml logs -f api
```

### Stop Staging Environment
```bash
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml down
```

### Restart Staging Service
```bash
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml restart api
```

---

## 5. Database Migrations

### Run Migrations on Staging
```bash
# Automatic (part of deploy script)
./scripts/deploy-staging.sh <sha>

# Manual
docker compose -p app-staging \
  -f docker-compose.prod.yml \
  -f compose.staging.yml \
  --env-file .env.staging \
  run --rm migrate
```

### Check Migration Status
```bash
docker compose -p app-staging \
  -f docker-compose.prod.yml \
  -f compose.staging.yml \
  --env-file .env.staging \
  run --rm api alembic current
```

---

## 6. Rollback Procedures

### Rollback Staging (GitHub Actions)
1. Go to **Actions** tab in GitHub
2. Click **Build and Deploy** workflow
3. Click **Run workflow**
4. Select:
   - Environment: `staging`
   - Action: `rollback`
   - Target SHA: (leave empty for previous, or specify SHA)
5. Click **Run workflow**

### Rollback Staging (SSH)
```bash
ssh user@vps
cd ~/app

# Rollback to previous version
./scripts/rollback-staging.sh

# Rollback to specific SHA
./scripts/rollback-staging.sh sha-abc123def456
```

---

## 7. Monitoring & Debugging

### Health Check
```bash
curl https://staging.joefoxing.com/health
```

### Check Container Health
```bash
docker inspect app-staging-api | jq '.[0].State.Health'
docker inspect app-staging-web | jq '.[0].State.Health'
```

### View Container Resources
```bash
docker stats app-staging-api app-staging-web app-staging-proxy
```

### Access Container Shell
```bash
docker exec -it app-staging-api /bin/sh
```

---

## 8. Security Considerations

### Optional: Basic Auth for Staging
Uncomment in `Caddyfile.staging`:
```caddyfile
basicauth {
    {$BASIC_AUTH_USER} {$BASIC_AUTH_PASSWORD}
}
```

Then add to `.env.staging`:
```bash
BASIC_AUTH_USER=staging
BASIC_AUTH_PASSWORD=<strong-password>
```

Restart proxy:
```bash
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml restart proxy
```

### IP Allowlist (Alternative)
In `Caddyfile.staging`, add:
```caddyfile
@blocked not remote_ip 1.2.3.4 5.6.7.8
abort @blocked
```

---

## 9. Troubleshooting

### Containers Won't Start
```bash
# Check logs
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml logs

# Check env file
cat .env.staging | grep -v "SECRET\|PASSWORD"

# Verify network
docker network ls | grep staging
```

### Database Connection Issues
```bash
# Test connection from container
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml \
  run --rm api python -c "from sqlalchemy import create_engine; import os; \
  engine = create_engine(os.environ['DATABASE_URL']); \
  conn = engine.connect(); print('Connected!')"
```

### Port Conflicts
Staging uses different ports to avoid conflicts:
- Proxy: 8080 (HTTP), 8443 (HTTPS) instead of 80/443
- Containers communicate via Docker network (no host port conflicts)

### Health Checks Failing
```bash
# Check from inside container
docker exec app-staging-api wget -O- http://localhost:8000/health

# Check proxy routing
docker exec app-staging-proxy wget -O- http://app-staging-api:8000/health
```

---

## 10. Comparison: Staging vs Production

| Aspect | Staging | Production |
|--------|---------|------------|
| **Domain** | staging.joefoxing.com | joefoxing.com |
| **Branch** | `develop` | `main` |
| **Database** | Separate Neon DB | Production Neon DB |
| **Compose Project** | `app-staging` | `app-prod` |
| **Network Subnet** | 172.21.0.0/16 | 172.20.0.0/16 |
| **Container Names** | `app-staging-*` | `app-*` |
| **Volumes** | `caddy_staging_data` | `caddy_data` |
| **Env File** | `.env.staging` | `.env.prod` |
| **Deploy Script** | `deploy-staging.sh` | `deploy.sh` |
| **Log Level** | DEBUG | INFO |
| **Resource Limits** | Lower (256M API) | Higher (512M API) |
| **Basic Auth** | Optional (recommended) | No |
| **Search Indexing** | Blocked (X-Robots-Tag) | Allowed |

---

## 11. Data Management

### DO NOT Copy Production Data to Staging
Production data may contain:
- Real user PII
- Payment information
- Sensitive business data

### Recommended Approaches:
1. **Synthetic data**: Use seed scripts with fake data
2. **Sanitized snapshots**: Strip PII if you must copy prod data
3. **Minimal fixtures**: Just enough data to test features

### Seed Staging Database
```bash
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml \
  run --rm api python scripts/seed_staging.py
```

---

## 12. Quick Reference Commands

```bash
# Deploy staging
./scripts/deploy-staging.sh <sha>

# Rollback staging
./scripts/rollback-staging.sh [sha]

# View staging logs
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml logs -f

# Restart staging
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml restart

# Stop staging
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml down

# Run migrations
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml run --rm migrate

# Health check
curl https://staging.joefoxing.com/health
```

---

## Next Steps

1. ✅ Set up DNS record for `staging.joefoxing.com`
2. ✅ Create separate Neon database for staging
3. ✅ Configure GitHub environments and secrets
4. ✅ Create `.env.staging` on VPS with different credentials
5. ✅ Test deployment: push to `develop` branch
6. ✅ Verify staging is accessible at `https://staging.joefoxing.com`
7. ✅ Test rollback procedure
8. ✅ Document any project-specific setup in team wiki

---

## Support

For issues or questions:
- Check logs: `docker compose -p app-staging ... logs`
- Review GitHub Actions workflow runs
- Verify environment variables and secrets
- Ensure database credentials are correct and separate from production
