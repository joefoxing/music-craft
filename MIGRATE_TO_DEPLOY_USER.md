# Migration Guide: Root → Deploy User

This guide walks you through transitioning from deploying as `root` to using a dedicated `deploy` user for your Docker-based application.

## Overview

**Current state:** Deploying as `root` user  
**Target state:** Deploying as `deploy` user with proper permissions  
**Impact:** No downtime required; can be done incrementally

---

## Part 1: Server-Side Setup (Run on VPS)

### Step 1: Create Deploy User

```bash
# As root, create the deploy user
sudo useradd -m -s /bin/bash deploy

# Add deploy to docker group (required for Docker commands)
sudo usermod -aG docker deploy

# Verify docker group membership
groups deploy
# Should show: deploy : deploy docker
```

### Step 2: Set Up SSH Access

```bash
# Create SSH directory for deploy user
sudo mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh

# Copy your SSH public key to deploy user
# Option A: Copy from root's authorized_keys
sudo cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys

# Option B: Or add your key manually
sudo nano /home/deploy/.ssh/authorized_keys
# Paste your public key, save and exit

# Set correct permissions
sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
```

### Step 3: Test SSH Access

```bash
# From your local machine, test SSH connection
ssh deploy@YOUR_SERVER_IP

# If successful, you should see deploy's shell prompt
# Exit and continue
exit
```

### Step 4: Migrate Application Directory

```bash
# As root, move the app directory to deploy's home
sudo mv /root/app /home/deploy/app

# Set ownership
sudo chown -R deploy:deploy /home/deploy/app

# Verify permissions
ls -la /home/deploy/app
```

### Step 5: Migrate Environment Files

```bash
# Move and set ownership of env files
sudo chown deploy:deploy /home/deploy/app/.env.prod
sudo chown deploy:deploy /home/deploy/app/.env.staging

# Secure permissions (readable only by deploy)
sudo chmod 600 /home/deploy/app/.env.prod
sudo chmod 600 /home/deploy/app/.env.staging
```

### Step 6: Verify Docker Access

```bash
# Switch to deploy user
sudo su - deploy

# Test Docker access
docker ps
docker network ls

# Verify you can see existing containers
docker compose -f ~/app/compose.prod.yml ps
docker compose -f ~/app/compose.staging.yml ps

# Exit back to root
exit
```

### Step 7: Update Docker Volume Permissions (if needed)

```bash
# Check current volume ownership
docker volume inspect app_prod_caddy_data
docker volume inspect app_prod_caddy_config

# Docker volumes are typically owned by root, which is fine
# The deploy user can manage containers that use these volumes
# No action needed unless you encounter permission errors
```

### Step 8: Test Deployment as Deploy User

```bash
# Switch to deploy user
sudo su - deploy

# Navigate to app directory
cd ~/app

# Test a staging deployment (use current SHA from .env.staging)
IMAGE_TAG=$(grep IMAGE_TAG .env.staging | cut -d= -f2)
bash scripts/deploy-staging.sh ${IMAGE_TAG#sha-}

# If successful, verify health
curl -I https://staging.joefoxing.com/health

# Exit back to root
exit
```

---

## Part 2: Update GitHub Actions (Run Locally)

### Step 1: Update Repository Variables

Go to your GitHub repository → Settings → Secrets and variables → Actions → Variables

**Update these variables:**

| Variable | Old Value | New Value |
|----------|-----------|-----------|
| `PROD_USER` | `root` | `deploy` |
| `STAGING_USER` | `root` | `deploy` |

### Step 2: Verify SSH Key

Ensure your `SSH_PRIVATE_KEY` secret matches the public key you added to `/home/deploy/.ssh/authorized_keys`

If you need to generate a new key pair:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/deploy_key

# Copy public key to server
ssh-copy-id -i ~/.ssh/deploy_key.pub deploy@YOUR_SERVER_IP

# Add private key to GitHub Secrets
cat ~/.ssh/deploy_key
# Copy output and add as SSH_PRIVATE_KEY secret in GitHub
```

### Step 3: Test GitHub Actions Deployment

1. Make a small commit to `develop` branch
2. Push to trigger staging deployment
3. Monitor GitHub Actions workflow
4. Verify deployment succeeds with deploy user

---

## Part 3: Verification Checklist

Run these checks to ensure everything works:

### ✅ SSH Access
```bash
ssh deploy@YOUR_SERVER_IP
# Should connect without password
```

### ✅ Docker Permissions
```bash
ssh deploy@YOUR_SERVER_IP "docker ps"
# Should list running containers
```

### ✅ Application Access
```bash
ssh deploy@YOUR_SERVER_IP "ls -la ~/app"
# Should show app directory owned by deploy:deploy
```

### ✅ Deployment Scripts
```bash
ssh deploy@YOUR_SERVER_IP "cd ~/app && bash scripts/deploy-staging.sh --help"
# Should show usage without permission errors
```

### ✅ Container Management
```bash
ssh deploy@YOUR_SERVER_IP "docker compose -f ~/app/compose.prod.yml ps"
# Should show production containers
```

### ✅ Health Endpoints
```bash
curl -I https://joefoxing.com/health
curl -I https://staging.joefoxing.com/health
# Both should return 200 OK
```

---

## Part 4: Rollback Plan (If Needed)

If you encounter issues and need to revert:

### Quick Rollback to Root

```bash
# As root on server
sudo mv /home/deploy/app /root/app
sudo chown -R root:root /root/app

# Revert GitHub Actions variables
# PROD_USER: deploy → root
# STAGING_USER: deploy → root
```

---

## Security Best Practices

### ✅ Completed by This Migration
- ✅ Dedicated non-root user for deployments
- ✅ Docker group membership (minimal required privilege)
- ✅ Restricted SSH key access
- ✅ Secure environment file permissions (600)

### 🔒 Additional Recommendations
- Consider using `sudo` with specific commands if deploy needs elevated privileges
- Rotate SSH keys periodically
- Enable SSH key-only authentication (disable password auth)
- Set up fail2ban for SSH brute-force protection
- Use UFW or iptables to restrict ports

---

## Troubleshooting

### Issue: "Permission denied" when running docker commands
```bash
# Verify deploy is in docker group
groups deploy

# If not, add and restart session
sudo usermod -aG docker deploy
# Log out and log back in
```

### Issue: "Cannot connect to Docker daemon"
```bash
# Check Docker service status
sudo systemctl status docker

# Ensure docker.sock has correct permissions
ls -la /var/run/docker.sock
# Should show: srw-rw---- 1 root docker

# Restart Docker if needed
sudo systemctl restart docker
```

### Issue: GitHub Actions deployment fails with "Host key verification failed"
```bash
# On your local machine (or in GitHub Actions)
ssh-keyscan -H YOUR_SERVER_IP >> ~/.ssh/known_hosts

# Or update the workflow to always accept (less secure)
# Add to deploy step: ssh -o StrictHostKeyChecking=no
```

### Issue: Environment files not found
```bash
# Verify files exist and are readable
sudo su - deploy
ls -la ~/app/.env.*
cat ~/app/.env.staging  # Should display contents

# If permission denied, fix ownership
exit  # back to root
sudo chown deploy:deploy /home/deploy/app/.env.*
sudo chmod 600 /home/deploy/app/.env.*
```

### Issue: Docker network overlap error
```
Error response from daemon: invalid pool request: Pool overlaps with other one on this address space
```

**Cause:** Old networks from previous deployments (possibly as root) conflict with new networks.

**Fix:**
```bash
# As deploy user
cd ~/app

# List all networks
docker network ls

# Remove old staging/prod networks (safe - will be recreated)
docker network rm app-staging_backend 2>/dev/null || true
docker network rm app_staging_default 2>/dev/null || true
docker network rm app-prod_backend 2>/dev/null || true
docker network rm app_prod_default 2>/dev/null || true

# Clean up unused networks
docker network prune -f

# Retry deployment
bash scripts/deploy-staging.sh <SHA>
```

**Permanent fix:** The compose files now include explicit subnet configurations:
- Production: `172.19.0.0/16`
- Staging: `172.20.0.0/16`

This prevents auto-assigned subnets from overlapping.

---

## Post-Migration Cleanup

After confirming everything works for 1-2 weeks:

```bash
# Remove root's old app directory (if you moved it)
# ONLY do this after verifying deploy user works perfectly
sudo rm -rf /root/app.backup  # if you created a backup

# Review and remove any old root crontabs related to the app
sudo crontab -l

# Audit root's SSH authorized_keys
sudo nano /root/.ssh/authorized_keys
# Consider removing keys that should only access deploy user
```

---

## Summary

**Before:**
- Deploying as `root` user
- App in `/root/app`
- GitHub Actions connects as `root`

**After:**
- Deploying as `deploy` user
- App in `/home/deploy/app`
- GitHub Actions connects as `deploy`
- Improved security posture
- Same functionality, better isolation

**Next Steps:**
1. Complete server-side setup (Part 1)
2. Update GitHub variables (Part 2)
3. Run verification checklist (Part 3)
4. Monitor deployments for 1-2 weeks
5. Clean up old root artifacts (Part 4)
