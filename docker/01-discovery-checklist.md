# Production Dockerization - Discovery Checklist

> **Purpose**: Complete this checklist before beginning migration to understand current production state.

## 1. Service Orchestration

- [ ] **Process manager**: systemd / pm2 / supervisor / circus / other: ___
- [ ] **Service definitions location**: `/etc/systemd/system/` / `ecosystem.config.js` / other: ___
- [ ] **Auto-start on boot**: Yes / No
- [ ] **User services run as**: `www-data` / `ubuntu` / `app` / other: ___

## 2. Domains & TLS

- [ ] **Primary domain**: `___`
- [ ] **Reverse proxy**: Caddy / Nginx / Apache / Traefik / Cloudflare (no local proxy)
- [ ] **TLS termination**: Local proxy / Cloudflare / AWS ALB / other: ___
- [ ] **Certificate management**: Caddy auto-TLS / Certbot / Manual / Managed LB
- [ ] **Static asset serving**: Via app / Via proxy / CDN (Cloudflare/S3)

## 3. Process Topology

Document each component:

| Service | Type | Port | Command | Critical? |
|---------|------|------|---------|-----------|
| API | HTTP server | 8000 | `uvicorn main:app` | Yes |
| Frontend | Static/SSR | 3000 | `next start` / `serve -s build` | Yes |
| Worker | Background job | N/A | `celery worker` / `python worker.py` | Maybe |
| Scheduler | Cron-like | N/A | `celery beat` / system cron | Maybe |
| WebSocket | WS server | 8080 | Same as API / Separate | Maybe |

## 4. Environment & Secrets

- [ ] **Current env file location**: `___`
- [ ] **Secrets managed by**: Ansible / Chef / Manual / .env file / Vault / AWS SM
- [ ] **Database URL format**: `postgresql://...` / Connection string in env / IAM auth
- [ ] **Additional secrets**: Redis password / S3 keys / API keys / JWT secret

## 5. Logging

- [ ] **Application logs**: stdout / file / syslog / journald
- [ ] **Log location**: `___`
- [ ] **Log rotation**: logrotate / journald / None (manual cleanup)
- [ ] **Centralized logging**: Datadog / CloudWatch / ELK / None

## 6. Health & Monitoring

- [ ] **Health endpoint**: `GET /health` / `GET /healthz` / `GET /api/health` / None
- [ ] **Health check logic**: Basic ping / Deep check (DB, cache)
- [ ] **Current monitoring**: Uptime Robot / Datadog / Prometheus / None
- [ ] **Alert channels**: Email / PagerDuty / Slack / None

## 7. Database & Migrations

- [ ] **Migration tool**: Alembic / Prisma / Knex / Django / Flyway / Other: ___
- [ ] **Migration command**: `alembic upgrade head` / `prisma migrate deploy` / ___
- [ ] **Migration runs**: At deploy / Manual / CI/CD / Never (schema managed externally)
- [ ] **Current schema version**: `___`

## 8. File Storage

- [ ] **User uploads**: Local disk `/var/www/uploads` / S3 / GCS / R2
- [ ] **Static files**: Local build output / S3 with CloudFront / Vercel
- [ ] **Temporary files**: `/tmp` / App-managed cleanup / Ephemeral only

## 9. Networking

- [ ] **App exposed ports**: `___`
- [ ] **Internal services**: Redis (localhost:6379) / RabbitMQ / None
- [ ] **Firewall (ufw/iptables)**: Active rules: ___
- [ ] **VPC/Security groups**: Cloud provider managed / N/A

## 10. Backup & Recovery

- [ ] **Database backups**: Managed provider (Neon) / Self-managed pg_dump
- [ ] **PITR available**: Yes (Neon) / No
- [ ] **File backup strategy**: ___
- [ ] **Recovery time objective (RTO)**: ___ minutes

---

## Assumptions for This Migration Plan

The following assumptions are made. **Review and adjust before execution:**

1. **Application Stack**: Python (FastAPI/Flask/Django) + Node.js frontend (React/Vue/Next.js)
2. **Database**: Managed Postgres (Neon) with connection pooling recommended
3. **No Redis/Cache**: If you use Redis, add a `redis` service to compose
4. **No message queue**: If using Celery/RQ, add worker service and broker
5. **Static uploads**: User uploads go to object storage (S3/R2), not local disk
6. **Reverse proxy**: Caddy (simple, automatic HTTPS) - swappable for Nginx
7. **Deployment target**: Single VPS/cloud instance (can extend to multiple)
8. **Git provider**: GitHub (for Actions workflow)
9. **Container registry**: GitHub Container Registry (ghcr.io) or Docker Hub
