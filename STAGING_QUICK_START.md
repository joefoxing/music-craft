# Staging Environment - Quick Start

Fast-track guide to get staging up and running in 15 minutes.

## Prerequisites
- VPS with Docker and Docker Compose installed
- DNS access to create `staging.joefoxing.com` A record
- Separate Neon database created for staging
- GitHub repo with Actions enabled

---

## Step 1: DNS (2 minutes)
Add A record:
```
staging.joefoxing.com → <YOUR_VPS_IP>
```

---

## Step 2: Neon Database (3 minutes)
1. Create new Neon project: `lyric-cover-staging`
2. Copy connection string (starts with `postgresql://`)
3. Keep it handy for Step 4

---

## Step 3: GitHub Setup (3 minutes)

### Create `staging` Environment
**Settings → Environments → New environment** → Name: `staging`

### Add Variables to `staging` environment:
```
STAGING_DOMAIN=staging.joefoxing.com
STAGING_HOST=<your-vps-ip>
STAGING_USER=<ssh-username>
```

### Ensure `production` environment has:
```
DOMAIN=joefoxing.com
PROD_HOST=<your-vps-ip>
PROD_USER=<ssh-username>
```

### Secrets (both environments share):
- `SSH_PRIVATE_KEY` (already configured for production)

---

## Step 4: VPS Setup (5 minutes)

```bash
# SSH into VPS
ssh user@your-vps
cd ~/app

# Create staging env file
cp .env.staging.example .env.staging

# Edit with your values
nano .env.staging
```

**Minimum required values in `.env.staging`:**
```bash
IMAGE_TAG=sha-latest  # Will be updated by CI/CD
REGISTRY=ghcr.io
REPO_OWNER=<your-github-username>
REPO_NAME=Lyric_Cover

DOMAIN=staging.joefoxing.com
APP_ENV=staging

# CRITICAL: Use staging database, NOT production
DATABASE_URL=postgresql://user:pass@staging-host/staging_db?sslmode=require

# Generate new secrets (different from production!)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET=$(openssl rand -hex 32)
```

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin
```

---

## Step 5: First Deploy (2 minutes)

### Option A: Automatic (Recommended)
```bash
# On your local machine
git checkout develop
git add .
git commit -m "Initial staging setup"
git push origin develop
```

Watch GitHub Actions deploy to staging automatically.

### Option B: Manual
```bash
# On VPS
cd ~/app
git checkout develop
git pull

# Get latest commit SHA
GIT_SHA=$(git rev-parse HEAD | cut -c1-12)

# Deploy
./scripts/deploy-staging.sh $GIT_SHA
```

---

## Step 6: Verify (1 minute)

```bash
# Check health
curl https://staging.joefoxing.com/health

# View containers
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml ps

# Check logs
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml logs -f
```

---

## Daily Workflow

### Deploy to Staging
```bash
git checkout develop
git add .
git commit -m "Feature: new feature"
git push origin develop
# Automatically deploys to staging
```

### Deploy to Production
```bash
git checkout main
git merge develop
git push origin main
# Automatically deploys to production
```

### Rollback Staging
**GitHub Actions → Run workflow → Select:**
- Environment: `staging`
- Action: `rollback`

---

## Troubleshooting

### "Health checks failed"
```bash
# Check logs
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml logs api

# Verify database connection
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml \
  run --rm api python -c "import os; print(os.environ.get('DATABASE_URL'))"
```

### "Cannot connect to staging.joefoxing.com"
```bash
# Check DNS propagation
dig staging.joefoxing.com

# Check Caddy logs
docker compose -p app-staging -f docker-compose.prod.yml -f compose.staging.yml logs proxy
```

### "Images not found"
```bash
# Verify registry login
docker login ghcr.io

# Check image exists
docker pull ghcr.io/<owner>/Lyric_Cover/api:sha-<commit>
```

---

## Key Differences from Production

| | Staging | Production |
|---|---|---|
| **Branch** | `develop` | `main` |
| **Domain** | staging.joefoxing.com | joefoxing.com |
| **Database** | Separate Neon DB | Production Neon DB |
| **Secrets** | Different values | Production values |
| **Containers** | `app-staging-*` | `app-*` |

---

## Next Steps

✅ Staging is now running!

1. Test a feature deployment to staging
2. Verify staging works as expected
3. Promote to production via `main` branch
4. Set up basic auth (optional): See `STAGING_SETUP_GUIDE.md` section 8

For detailed documentation, see `STAGING_SETUP_GUIDE.md`
