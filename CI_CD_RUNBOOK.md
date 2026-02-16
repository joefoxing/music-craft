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

### 3.2. Directory Structure
Create the application directory:
```bash
mkdir -p ~/app/scripts
cd ~/app
```
*Note: The server is treated as a runtime environment. We do NOT pull the full git repository source code to run the app, only the orchestration files.*

### 3.3. Environment Configuration
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

### 3.4. Orchestration Files
Copy the `compose.prod.yml` (or `compose.staging.yml`) and `scripts/` folder to `~/app` on the server.
*   **Staging:** `compose.staging.yml`
*   **Production:** `compose.prod.yml`

Make scripts executable:
```bash
chmod +x scripts/*.sh
```

---

## 4. The CI/CD Pipeline (`deploy.yml`)

The pipeline is defined in `.github/workflows/deploy.yml`.

### Triggers & Flow
1.  **Push to `main`**:
    *   Builds and Pushes Docker Image to GHCR.
    *   **Auto-deploys to Staging**.
2.  **Verify Staging**:
    *   Manual verification of Staging environment.
3.  **Manual Promotion to Production**:
    *   Triggered via GitHub Actions "Run workflow" (workflow_dispatch).
    *   Requires selecting `production` environment and providing the **exact SHA** that passed staging.

### Job Breakdown
1.  **`build-and-push`** (Push to `main`):
    *   Builds `Dockerfile.api`.
    *   Tags with `sha-<short_commit_hash>` and `latest`.
    *   Pushes to GHCR.
    *   **Output**: Passes the `short_sha`.

2.  **`deploy-staging`** (Automatic after build):
    *   SSHs into `STAGING_HOST`.
    *   Updates `IMAGE_TAG` in `.env.staging`.
    *   Executes `bash scripts/deploy-staging.sh <SHA>`.

3.  **`deploy-production`** (Manual Workflow Dispatch):
    *   SSHs into `PROD_HOST`.
    *   Updates `IMAGE_TAG` in `.env.prod`.
    *   Executes `bash scripts/deploy.sh <SHA>`.

---

## 5. Deployment Scripts Logic

### `scripts/deploy.sh` (Production) & `scripts/deploy-staging.sh`
1.  **Locking**: Uses `flock` to prevent concurrent deployments.
2.  **Version Tracking**:
    *   Shifts `DEPLOYED_SHA_<ENV>.txt` to `DEPLOYED_SHA_<ENV>.txt.prev`.
3.  **Pull**: `docker compose pull api`. **(No git pull)**.
4.  **Update**: `docker compose up -d --remove-orphans api`.
    *   **Note**: Migrations are **NOT** run automatically.
5.  **Health Check**: Loops checking container health.
    *   **Success**: Writes new SHA to `DEPLOYED_SHA_<ENV>.txt` and logs success.
    *   **Failure**: Automatically triggers rollback using `.prev` SHA.
6.  **External Verification**:
    *   Curls `https://<domain>/health` to ensure the service is reachable via the reverse proxy.

---

## 6. Database Migrations (Explicit Only)

Migrations are **never** run automatically during deployment. They must be triggered manually when needed.

### Running Migrations via GitHub Actions
1.  Go to GitHub Actions -> "Run Migrations".
2.  Run workflow.
3.  Select Environment: `staging` or `production`.

### Running Migrations Manually (SSH)
Connect to the server and run the migration profile:

**Staging:**
```bash
docker compose -f compose.staging.yml --env-file .env.staging --profile migrate run --rm migrate
```

**Production:**
```bash
docker compose -f compose.prod.yml --env-file .env.prod --profile migrate run --rm migrate
```

---

## 7. Manual Operations & Debugging

### Triggering a Manual Production Deploy
1.  Go to GitHub Actions tab.
2.  Select "Build and Deploy".
3.  Click "Run workflow".
4.  Environment: `production`.
5.  Image Tag: Enter the SHA you want to deploy (e.g., `a1b2c3d4e5f6`).

### Triggering a Rollback
If a deployment fails and the auto-rollback fails, or you need to revert to a previous version:
1.  Identify the target Commit SHA you want to revert to.
2.  Run the manual deploy workflow (as above) with the old SHA.

### Accessing Logs
SSH into the server:
```bash
ssh user@host
cd ~/app

# View API logs
docker compose -f compose.prod.yml --env-file .env.prod logs -f api
```

---

## 8. Troubleshooting

### "alembic: command not found" or Migration Fails
**Fix**: Ensure you are using the `--profile migrate` flag as shown in Section 6. Check `DATABASE_URL` in `.env`.

### Health Check Timeout
**Cause**: The application failed to start within 120 seconds or the external URL is unreachable.
**Fix**:
1.  Check container logs: `docker compose ... logs api`.
2.  Check if Caddy/Proxy is running and properly routing.

### GHCR Permission Denied
**Fix**: Ensure the `GHCR_TOKEN` secret in GitHub has `write:packages` scope and the workflow has logged in successfully.