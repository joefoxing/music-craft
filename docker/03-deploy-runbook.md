# Production Migration + Deploy Runbook

> **Purpose**: Step-by-step guide for migrating from current production to Docker Compose-based deployment with zero/low downtime.

## Prerequisites

- [ ] Completed `01-discovery-checklist.md` - understand current state
- [ ] Access to production server (SSH key configured)
- [ ] Access to Neon database dashboard
- [ ] GitHub repository with Actions enabled
- [ ] Domain DNS managed (can update records if needed)
- [ ] Sufficient disk space on server (~5GB free for images)

---

## Phase 1: Pre-Migration Preparation

### 1.1 Create Backups & Verify Recovery

```bash
# On production database (Neon)
# 1. Log into Neon dashboard
# 2. Create a manual snapshot named: "pre-docker-migration-$(date +%Y%m%d)"
# 3. Note the snapshot ID for reference

# Verify PITR is enabled and retention period
# Neon Standard plan: 7 days PITR
# Neon Pro plan: 30 days PITR
```

### 1.2 Document Current State

```bash
# SSH to production server and capture:

# Current running processes
ps aux | grep -E "(python|node|gunicorn|uvicorn)" > ~/migration-backup/processes.txt

# Current environment variables (sanitized)
env | grep -v PASSWORD | grep -v SECRET | grep -v KEY > ~/migration-backup/environment.txt

# Current open ports
ss -tlnp > ~/migration-backup/ports.txt

# Current disk usage
df -h > ~/migration-backup/disk.txt

# Current service status
systemctl list-units --type=service --state=running > ~/migration-backup/services.txt
```

### 1.3 Prepare the Target Server

```bash
# Install Docker (if not present)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose (v2 plugin)
docker compose version  # Should show v2.x.x

# Create project directory
mkdir -p ~/app && cd ~/app

# Clone repository (or use existing)
git clone https://github.com/OWNER/REPO.git .
```

### 1.4 Prepare Environment File

```bash
# Copy template and fill in real values
cp .env.prod.example .env.prod

# Edit with real secrets
nano .env.prod

# Validate required variables are set
grep -E "^(DOMAIN|DATABASE_URL|SECRET_KEY)=" .env.prod | cut -d'=' -f2 | wc -c
# Should show > 50 (values exist)
```

---

## Phase 2: Parallel Deployment (Verification)

### 2.1 Deploy on Alternate Ports

```bash
# Modify Caddyfile temporarily for port 8080/8443
cp Caddyfile Caddyfile.prod
sed -i 's/80:80/8080:80/g; s/443:443/8443:443/g' Caddyfile

# Update DOMAIN to use staging subdomain (optional)
# echo "staging.DOMAIN= staging.yourdomain.com" >> .env.prod

# Start the stack
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Check logs
docker compose -f docker-compose.prod.yml logs -f
```

### 2.2 Verify Stack Health

```bash
# Check all services are running
docker compose -f docker-compose.prod.yml ps

# Check health endpoints
curl http://localhost:8080/api/health
curl http://localhost:3000/health  # if exposed

# Verify can connect to Neon database
docker compose -f docker-compose.prod.yml exec api python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    engine = create_async_engine('${DATABASE_URL}', echo=True)
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT 1'))
        print('Database connection OK:', result.scalar())

asyncio.run(test())
"
```

### 2.3 Run Migrations (Test Mode)

```bash
# This runs migrations on the SAME database
# Ensure migrations are backwards-compatible!

docker compose -f docker-compose.prod.yml --env-file .env.prod \
    run --rm migrate

# Verify migration applied
# Check application still works with old code
```

### 2.4 Smoke Tests

```bash
# Test critical user flows via the alternate port
# Use hosts file to test with real domain:
echo "YOUR_SERVER_IP staging.yourdomain.com" | sudo tee -a /etc/hosts

# Then test:
# - Login flow
# - CRUD operations
# - File uploads (if applicable)
# - Background jobs (if applicable)
```

---

## Phase 3: Cutover (Low-Downtime Switch)

### 3.1 Announce Maintenance Window

- Notify users of brief maintenance (<5 minutes)
- Set status page if available
- Schedule during low-traffic period

### 3.2 Stop Old Services

```bash
# Stop current production processes
# Adjust based on your process manager:

# If using systemd:
sudo systemctl stop your-api-service
sudo systemctl stop your-web-service
sudo systemctl disable your-api-service  # Prevent auto-start

# If using pm2:
pm2 stop all
pm2 delete all

# If using supervisor:
sudo supervisorctl stop all

# Verify ports are free
ss -tlnp | grep -E "(80|443|8000|3000)"
```

### 3.3 Switch Docker Compose to Production Ports

```bash
cd ~/app

# Restore original Caddyfile
cp Caddyfile.prod Caddyfile

# Ensure ports are free (should be after stopping old services)
! ss -tlnp | grep -E ":80|:443" || echo "WARNING: Ports still in use"

# Start with production configuration
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Watch logs for startup
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

### 3.4 Verify Production Cutover

```bash
# Check services are healthy
docker compose -f docker-compose.prod.yml ps

# Test external access (from your machine)
curl -s https://yourdomain.com/health | jq .

# Verify TLS certificate
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Test a real user flow
# - Register/login
# - Create content
# - Verify in database
```

### 3.5 Monitor Post-Cutover

```bash
# Watch logs for errors (keep open for 10 minutes)
docker compose -f docker-compose.prod.yml logs -f --tail=50 | grep -E "(ERROR|WARN|CRITICAL)"

# Monitor resource usage
watch -n 2 'docker stats --no-stream'

# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://yourdomain.com/api/health
```

---

## Phase 4: Post-Migration

### 4.1 Cleanup Old Infrastructure

```bash
# Remove old systemd services (if applicable)
sudo rm /etc/systemd/system/your-api.service
sudo systemctl daemon-reload

# Remove old code directories (keep backup)
sudo mv /var/www/old-app ~/migration-backup/old-app-$(date +%Y%m%d)

# Remove old log files (if migrated to Docker)
sudo logrotate -f /etc/logrotate.d/old-app  # Force rotation first
sudo rm -rf /var/log/old-app/*
```

### 4.2 Update Monitoring

```bash
# Update health check monitors
# Point UptimeRobot/Datadog/whatever to:
# https://yourdomain.com/health

# Update alert destinations if changed
```

### 4.3 Document New Operations

```bash
# Add aliases for common operations to ~/.bashrc:

echo '
# Docker Compose aliases
alias dcp="docker compose -f ~/app/docker-compose.prod.yml --env-file ~/app/.env.prod"
alias dcplogs="dcp logs -f"
alias dcpps="dcp ps"
alias dcprestart="dcp restart"
' >> ~/.bashrc
```

---

## Rollback Procedures

### Scenario A: Immediate Rollback (within 5 minutes)

```bash
# If cutover fails immediately:

cd ~/app

# Stop Docker stack
docker compose -f docker-compose.prod.yml down

# Restart old services
sudo systemctl start your-api-service
sudo systemctl start your-web-service

# Verify old stack works
# Update DNS if you changed it
```

### Scenario B: Rollback to Previous Docker Image

```bash
# Use the rollback script
./scripts/rollback.sh

# Or manually:
cd ~/app

# Get previous SHA
cat .rollback-tag  # shows previous version

# Rollback to specific version
IMAGE_TAG=sha-ABC123 docker compose -f docker-compose.prod.yml up -d
```

### Scenario C: Database Rollback (Neon PITR)

```bash
# If database corruption/migration issue:
# 1. Log into Neon console
# 2. Navigate to your project
# 3. Go to "Branches" or "Restore"
# 4. Select PITR point before migration
# 5. Restore to new branch or replace main branch
# 6. Update DATABASE_URL in .env.prod if branch changed
# 7. Restart Docker stack
```

---

## Migration Verification Checklist

- [ ] Website loads with valid HTTPS certificate
- [ ] Login/authentication works
- [ ] Database queries return expected data
- [ ] Background jobs process (if applicable)
- [ ] File uploads work (if applicable)
- [ ] Email sending works (if applicable)
- [ ] API endpoints respond correctly
- [ ] No ERROR/WARNING logs in 30 minutes post-deploy
- [ ] Memory usage stable (not growing unbounded)
- [ ] Can successfully rollback if needed

---

## Ongoing Operations

### Daily
```bash
# Quick health check
curl -s https://yourdomain.com/health | jq .
docker compose -f docker-compose.prod.yml ps
```

### Weekly
```bash
# Review logs for errors
docker compose -f docker-compose.prod.yml logs --since=7d | grep -i error

# Clean up old images
docker system prune -f
```

### Monthly
```bash
# Update base images and redeploy
# (Create PR to update Dockerfile base image tags)
```
