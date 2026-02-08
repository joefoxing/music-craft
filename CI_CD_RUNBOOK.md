# CI/CD & Deployment Runbook

This document details the exact step-by-step pipeline for building and deploying the Lyric Cover application to Staging and Production environments.

## 1. System Architecture

*   **Source Control:** GitHub
*   **CI/CD:** GitHub Actions
*   **Registry:** GitHub Container Registry (GHCR)
*   **Infrastructure:** VPS (Ubuntu/Debian recommended)
*   **Orchestration:** Docker Compose
*   **Reverse Proxy:** Caddy (Running as a system service or container)

---

## 2. GitHub Configuration

### Environment Variables & Secrets
Ensure these are set in the GitHub Repository Settings -> Secrets and variables.

| Name | Type | Description |
|------|------|-------------|
| `GHCR_TOKEN` | Secret | Personal Access Token (PAT) with `read:packages` and `write:packages` scopes to push to GHCR. |
| `SSH_PRIVATE_KEY` | Secret | Private SSH key for accessing the VPS. The public key must be in `~/.ssh/authorized_keys` on the server. |
| `DOMAIN` | Variable | Production domain (e.g., `example.com`). |
| `PROD_HOST` | Variable | IP address or hostname of the Production VPS. |
| `PROD_USER` | Variable | SSH username for Production (e.g., `deploy` or `root`). |
| `STAGING_DOMAIN` | Variable | Staging domain (e.g., `staging.example.com`). |
| `STAGING_HOST` | Variable | IP address or hostname of the Staging VPS. |
| `STAGING_USER` | Variable | SSH username for Staging. |

---

## 3. Server Setup (One-Time)

Perform these steps on both Staging and Production servers.

### 3.1. Prerequisites
Install Docker and Docker Compose on the server.
```bash
# Example for Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### 3.2. Network Setup
The `compose.prod.yml` expects an external network named `proxy_net`.
```bash
docker network create proxy_net
```

### 3.3. Directory Structure
Create the application directory:
```bash
mkdir -p ~/app/scripts
cd ~/app
```

### 3.4. Environment Configuration
Create the environment specific files (`.env.prod` for production, `.env.staging` for staging).

**Example `.env.prod`:**
```ini
# App
APP_ENV=production
SECRET_KEY=change_this_to_a_secure_random_string
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@db_host:5432/dbname

# External Services (Optional)
REDIS_URL=redis://redis_host:6379/0
S3_BUCKET=my-bucket
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
S3_ENDPOINT=https://s3.region.amazonaws.com

# Deployment (Managed by CI, but initial value needed)
IMAGE_TAG=latest
REGISTRY=ghcr.io
REPO_OWNER=your_github_username
REPO_NAME=music-craft
```

### 3.5. Scripts
Ensure the `scripts/` directory on the server contains the deployment scripts. The CI pipeline will pull the latest code, but the scripts must be executable.
```bash
chmod +x scripts/*.sh
```

---

## 4. The CI/CD Pipeline (`deploy.yml`)

The pipeline is defined in `.github/workflows/deploy.yml`.

### Triggers
1.  **Push to `main`**: Deploys to **Production**.
2.  **Push to `develop`**: Deploys to **Staging**.
3.  **Manual Dispatch**: Allows manual deployment or rollback to specific environments.

### Job Breakdown
1.  **`build`**:
    *   Checks out code.
    *   Builds the Docker image using `Dockerfile.api`.
    *   Tags image with `sha-<short_commit_hash>` and `latest`.
    *   Pushes to GHCR.
    *   **Output**: Passes the `sha` to deployment jobs.

2.  **`deploy-staging`** (Runs on `develop` branch):
    *   SSHs into `STAGING_HOST`.
    *   Pulls latest git changes to `~/app`.
    *   Updates `IMAGE_TAG` in `.env.staging`.
    *   Executes `bash scripts/deploy-staging.sh <SHA>`.

3.  **`deploy-production`** (Runs on `main` branch):
    *   SSHs into `PROD_HOST`.
    *   Pulls latest git changes to `~/app`.
    *   Updates `IMAGE_TAG` in `.env.prod`.
    *   Executes `bash scripts/deploy.sh <SHA>`.

---

## 5. Deployment Scripts Logic

### `scripts/deploy.sh` (Production)
1.  **Locking**: Uses `flock` to prevent concurrent deployments.
2.  **Version Tracking**: Records the currently running image SHA into `.rollback-tag` before updating.
3.  **Pull**: Pulls the specific image tag (`sha-XXXXXX`).
4.  **Migrate**: Runs database migrations (`alembic upgrade head`) using the `migrate` profile/service.
5.  **Update**: Recreates the `api` container.
6.  **Health Check**: Loops checking container health.
    *   **Success**: Logs success.
    *   **Failure**: Automatically triggers `rollback.sh`.

---

## 6. Manual Operations & Debugging

### Triggering a Manual Deployment
1.  Go to GitHub Actions tab.
2.  Select "Build and Deploy".
3.  Click "Run workflow".
4.  Choose Branch: `main` (for prod) or `develop` (for staging).
5.  Environment: `production` or `staging`.
6.  Action: `deploy`.

### Triggering a Rollback
If a deployment fails and the auto-rollback fails, or you need to revert to a previous version:
1.  Identify the target Commit SHA you want to revert to (first 12 characters).
2.  Go to GitHub Actions -> "Build and Deploy" -> "Run workflow".
3.  Action: `rollback`.
4.  Target SHA: `<old_sha>`.

### Accessing Logs
SSH into the server:
```bash
ssh user@host
cd ~/app

# View API logs
docker compose -f compose.prod.yml --env-file .env.prod logs -f api

# View Migration logs
docker compose -f compose.prod.yml --env-file .env.prod logs -f migrate
```

### Entering the Container
```bash
docker compose -f compose.prod.yml --env-file .env.prod exec api /bin/bash
```

---

## 7. Troubleshooting

### "Error response from daemon: network proxy_net not found"
**Fix**: Run `docker network create proxy_net`.

### "alembic: command not found" or Migration Fails
**Fix**: Check logs: `docker compose ... logs migrate`. Ensure `DATABASE_URL` is correct in `.env.prod`.

### Health Check Timeout
**Cause**: The application failed to start within 120 seconds.
**Fix**: Check logs (`docker compose ... logs api`). Common causes: invalid `SECRET_KEY`, database connection failure, or missing dependencies.

### GHCR Permission Denied
**Fix**: Ensure the `GHCR_TOKEN` secret in GitHub has `write:packages` scope and the workflow has logged in successfully.
