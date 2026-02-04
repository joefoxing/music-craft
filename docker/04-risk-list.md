# Risk Assessment and Mitigations

> **Purpose**: Identify potential risks in the dockerization migration and their mitigations.

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation Status |
|------|------------|--------|-------------------|
| Data loss during migration | Low | Critical | ✅ Mitigated |
| Downtime exceeding SLA | Medium | High | ✅ Mitigated |
| Environment variable drift | Medium | Medium | ✅ Mitigated |
| Container image vulnerabilities | Medium | Medium | ✅ Mitigated |
| Database connection exhaustion | Medium | High | ✅ Mitigated |
| File upload path issues | Medium | Medium | ✅ Mitigated |
| TLS certificate problems | Low | High | ✅ Mitigated |
| Rollback failure | Low | Critical | ✅ Mitigated |

---

## Detailed Risk Analysis

### 1. Data Loss During Migration

**Description**: Accidental database corruption or deletion during the migration process.

**Likelihood**: Low (managed database with backups)
**Impact**: Critical (business data)

**Mitigations**:
- ✅ Use managed Postgres (Neon) with automatic backups
- ✅ Create explicit pre-migration snapshot
- ✅ Verify PITR (Point-in-Time Recovery) is enabled
- ✅ Test restore procedure before migration day
- ✅ No database container - always external service
- ✅ Database migrations are backwards-compatible (add-only before cutover)

**Contingency**:
- Restore from Neon snapshot within minutes
- PITR available for granular recovery

---

### 2. Extended Downtime

**Description**: Migration takes longer than expected, exceeding acceptable downtime window.

**Likelihood**: Medium (unexpected issues always possible)
**Impact**: High (user impact, SLA breach)

**Mitigations**:
- ✅ Parallel deployment strategy - verify on alternate ports first
- ✅ Clear rollback procedure ready (< 2 minutes to revert)
- ✅ Scheduled during low-traffic period
- ✅ Maintenance page capability (Caddy can serve static "under maintenance")
- ✅ All preparation done in advance (Docker installed, images pulled)

**Contingency**:
- Immediate rollback to old systemd/pm2 services
- Estimated rollback time: 30-60 seconds

---

### 3. Environment Variable Drift

**Description**: Secrets or config differ between old and new deployment, causing silent failures.

**Likelihood**: Medium (easy to miss obscure env vars)
**Impact**: Medium (feature failures, not data loss)

**Mitigations**:
- ✅ Comprehensive .env.prod.example template
- ✅ Document all environment variables with descriptions
- ✅ Compare old env vs new before migration
- ✅ Validation script to check required vars are set
- ✅ Same env file used by all containers (consistent)

**Verification**:
```bash
grep -E "^(DOMAIN|DATABASE_URL|SECRET_KEY)=" .env.prod | cut -d'=' -f2 | wc -c
# Should be > 0 for each required var
```

---

### 4. Container Image Vulnerabilities

**Description**: Base images contain known CVEs, creating security exposure.

**Likelihood**: Medium (new CVEs discovered regularly)
**Impact**: Medium (depends on exploitability)

**Mitigations**:
- ✅ Use minimal base images (alpine, slim variants)
- ✅ Pin exact image versions (not `latest`)
- ✅ Non-root user in containers
- ✅ Multi-stage builds reduce attack surface
- ✅ No build tools in production images
- ✅ Regular base image updates (monthly cadence)

**Monitoring**:
- Enable GitHub Dependabot for Docker
- Use `docker scan` or Trivy in CI pipeline

---

### 5. Database Connection Exhaustion

**Description**: Containerized app opens too many connections, exceeding Neon limits.

**Likelihood**: Medium (default connection pools often too large)
**Impact**: High (app becomes unresponsive)

**Mitigations**:
- ✅ Configure connection pooling (PgBouncer or SQLAlchemy pool)
- ✅ Set `POOL_SIZE` and `MAX_OVERFLOW` explicitly
- ✅ Use Neon's connection pooler endpoint if available
- ✅ Monitor connection count in Neon dashboard
- ✅ Set resource limits on containers (prevents runaway scaling)

**Recommended Settings**:
```python
# SQLAlchemy async example
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)
```

---

### 6. File Upload Path Issues

**Description**: Uploaded files don't persist or aren't accessible after migration.

**Likelihood**: Medium (path changes between deployments)
**Impact**: Medium (user uploads lost or broken)

**Mitigations**:
- ✅ Use object storage (S3/R2/GCS) for uploads, not local disk
- ✅ If local storage needed: Docker volume with correct permissions
- ✅ Pre-migration audit: list all upload locations
- ✅ Pre-migration: sync existing uploads to new location/object storage
- ✅ Non-root user has write permissions to upload directory

**Migration Path**:
```bash
# If migrating local uploads to S3
aws s3 sync /var/www/old-app/uploads/ s3://your-bucket/uploads/
```

---

### 7. TLS Certificate Problems

**Description**: HTTPS fails due to certificate issues, browser warnings, or Caddy misconfiguration.

**Likelihood**: Low (Caddy handles this automatically)
**Impact**: High (users can't access site securely)

**Mitigations**:
- ✅ Caddy automatic HTTPS (Let's Encrypt/ZeroSSL)
- ✅ DOMAIN env var must match DNS exactly
- ✅ Port 80 must be open for ACME challenge
- ✅ Test on staging subdomain first
- ✅ Certificate persistence via Docker volume (`caddy_data`)

**Verification**:
```bash
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
curl -vI https://yourdomain.com 2>&1 | grep "SSL certificate"
```

---

### 8. Rollback Failure

**Description**: Unable to rollback to previous version due to missing images, db incompatibility, or script failures.

**Likelihood**: Low (well-tested procedure)
**Impact**: Critical (stuck with broken deployment)

**Mitigations**:
- ✅ Always record rollback tag before deploy
- ✅ Images retained in registry (don't auto-delete)
- ✅ Rollback script tested in staging
- ✅ Database migrations are backwards-compatible
- ✅ Manual rollback procedure documented
- ✅ Old systemd services kept disabled (not deleted) for 24h

**Contingency**:
- Manual image pull and docker-compose up with old SHA
- Re-enable old systemd services as emergency fallback

---

## Pre-Migration Checklist

### Infrastructure
- [ ] Server has Docker 24.x+ and Compose v2
- [ ] Server has > 5GB free disk space
- [ ] Ports 80, 443 available (or alternate ports tested)
- [ ] SSH access configured for CI/CD

### Database
- [ ] Neon snapshot created
- [ ] PITR verified working
- [ ] Connection pool size configured
- [ ] Migration tested on copy of production data

### Application
- [ ] All env vars documented in .env.prod.example
- [ ] .env.prod created on server with real values
- [ ] Health endpoints implemented (`/health` on API and Web)
- [ ] Backwards-compatible migrations confirmed

### Files/Media
- [ ] Upload strategy: S3 vs local disk decided
- [ ] If local: volume path configured
- [ ] If S3: credentials configured, existing files synced

### Testing
- [ ] Parallel deployment tested on alternate ports
- [ ] Smoke tests pass (login, CRUD, uploads)
- [ ] Rollback script tested
- [ ] Log aggregation verified

---

## Post-Migration Monitoring

### Immediate (0-30 min)
- [ ] All containers show `healthy` status
- [ ] External health endpoint responds 200
- [ ] No ERROR level logs in container output
- [ ] Response times within normal range
- [ ] Can complete end-to-end user flow

### Short-term (1-24 hours)
- [ ] Memory usage stable (no leaks)
- [ ] No connection pool exhaustion
- [ ] Background jobs processing (if applicable)
- [ ] Error rate < 0.1%

### Long-term (ongoing)
- [ ] Weekly review of container security updates
- [ ] Monthly base image updates
- [ ] Log rotation working correctly
- [ ] Backup verification (test restore quarterly)

---

## Incident Response Contacts

| Issue | Contact | Action |
|-------|---------|--------|
| Database emergency | Neon support / PITR restore | Restore from snapshot |
| Server down | Your hosting provider | Check infrastructure |
| TLS issues | Caddy community / Let's Encrypt | Debug certificate |
| Application bug | Rollback procedure | Revert to last known good |

---

## Assumptions Requiring Validation

Before proceeding, confirm these assumptions:

1. **Single server deployment**: If you need multi-server, this architecture needs adjustment
2. **Neon Postgres**: If using different managed DB, verify connection string format
3. **No Redis/Cache**: If you use Redis, add it to docker-compose.prod.yml
4. **No message queue**: If using Celery with RabbitMQ/Redis, add broker service
5. **Caddy as proxy**: Can be swapped for Nginx if preferred
6. **GitHub Actions**: Adjust workflow if using GitLab CI, CircleCI, etc.
7. **Static uploads to S3**: Change strategy if using local disk storage

---

## Sign-off

Before migration day, obtain sign-off from:

- [ ] Technical lead (architecture review)
- [ ] Database administrator (migration plan)
- [ ] Product owner (acceptance of downtime window)
- [ ] Security review (Dockerfile scan, secrets management)

---

**Last Updated**: 2024
**Review Date**: After each deployment
