# Target Docker Compose Architecture

## Overview

The dockerized production stack uses **immutable images tagged by Git SHA**, ensuring repeatable deploys and easy rollback. Services communicate via an internal Docker network; only the reverse proxy exposes ports to the host.

## Architecture Diagram

```
                                    ┌─────────────────┐
                               443  │   Caddy Proxy   │ 80
                         ┌─────────►│  (reverse proxy)│◄────────┐
                         │          │  auto-TLS/HTTPS │         │
                         │          └────────┬────────┘         │
     Internet            │                   │                  │
    ═════════            │          ┌────────┴────────┐         │
                         │          │  internal net   │         │
                         │          │  (docker net)   │         │
                         │          └────────┬────────┘         │
                         │                   │                  │
                   ┌─────┴─────┐    ┌────────┴────────┐   ┌────┴────┐
                   │   API     │    │  Frontend/Web   │   │ Worker  │
                   │  (FastAPI)│    │   (Next.js/)    │   │(Celery/ │
                   │  :8000    │    │    :3000        │   │ RQ/etc) │
                   └─────┬─────┘    └─────────────────┘   └─────────┘
                         │
                         │  ┌─────────────────────────────────────┐
                         └──►  Managed Postgres (Neon)            │
                             │  - No container                     │
                             │  - Connection via DATABASE_URL      │
                             └─────────────────────────────────────┘
```

## Services

### 1. `proxy` (Caddy)
- **Purpose**: Reverse proxy, TLS termination, static file serving
- **Image**: `caddy:2.7-alpine` (pinned)
- **Ports**: `80:80`, `443:443` (host), `443:443/udp` (HTTP/3)
- **Volumes**: 
  - `./Caddyfile:/etc/caddy/Caddyfile`
  - `caddy_data:/data` (TLS certs)
  - `caddy_config:/config`
  - `./static:/srv/static` (if serving static locally)
- **Depends on**: `api`, `web` (for health)
- **Restart**: `unless-stopped`

### 2. `api`
- **Purpose**: Backend API server (Python FastAPI/Flask/Django)
- **Image**: `ghcr.io/owner/repo/api:sha-<GIT_SHA>` (immutable)
- **Expose**: Port 8000 (not published to host - internal only)
- **Environment**: Injected from `.env.prod`
- **Healthcheck**: `GET /health` every 30s
- **Restart**: `unless-stopped`
- **Resources**: Memory limits to prevent runaway growth

### 3. `web` (if separate frontend)
- **Purpose**: SSR frontend or static file server
- **Image**: `ghcr.io/owner/repo/web:sha-<GIT_SHA>`
- **Expose**: Port 3000 (internal)
- **Healthcheck**: `GET /` or `GET /health`
- **Restart**: `unless-stopped`

### 4. `worker` (background jobs)
- **Purpose**: Celery/RQ/ARQ worker processes
- **Image**: Same as `api` (shares code, different entrypoint)
- **Command override**: `celery -A tasks worker -l info`
- **No ports exposed**
- **Scale**: `docker compose up -d --scale worker=3`
- **Restart**: `unless-stopped`

### 5. `migrate` (one-off job)
- **Purpose**: Database migrations (runs then exits)
- **Image**: Same as `api`
- **Command override**: `alembic upgrade head` or equivalent
- **Profile**: `docker compose --profile migrate up migrate`
- **Never restarted**: One-shot container

## Networks

```yaml
networks:
  backend:
    driver: bridge
    internal: false  # Needs external access for DB
```

All services connect to `backend` network for inter-service communication.

## Key Design Decisions

### Immutable Images
- Every build produces images tagged with full Git SHA: `:sha-abc123def...`
- Never use `:latest` for production deploys (only for convenience)
- Deploy script references explicit SHA for reproducibility

### Database External
- No `postgres` service in compose
- Connect to Neon via `DATABASE_URL` env var
- Use connection pooling (PgBouncer or Neon's built-in pooler) to avoid connection limits

### Entrypoint Strategy

The API Dockerfile uses an entrypoint script that supports:
```bash
# Default: run app
docker compose up api

# Override: run migrations
docker compose run --rm api alembic upgrade head

# Override: run worker
docker compose run --rm api celery worker
```

### Healthchecks

Every long-running service has a healthcheck:
- **API**: `curl -f http://localhost:8000/health || exit 1`
- **Web**: `curl -f http://localhost:3000/health || exit 1`
- **Worker**: Process check or queue ping (tool-dependent)
- **Proxy**: Built-in Caddy health or upstream checks

### Log Strategy

- All containers log to **stdout/stderr** as structured JSON
- Docker captures logs via json-file driver (default)
- Log rotation configured in daemon.json or compose
- Optional: forward to centralized logging (Datadog, etc.)

## File Structure

```
project/
├── docker/
│   ├── 01-discovery-checklist.md
│   ├── 02-architecture.md (this file)
│   ├── 03-deploy-runbook.md
│   └── 04-risk-list.md
├── docker-compose.prod.yml
├── docker-compose.override.yml (local dev, gitignored)
├── .env.prod (server-side, never committed)
├── .env.prod.example (template)
├── .dockerignore
├── Dockerfile.api
├── Dockerfile.web (if needed)
├── Caddyfile
├── scripts/
│   ├── entrypoint.sh
│   ├── deploy.sh
│   └── rollback.sh
└── .github/
    └── workflows/
        └── deploy.yml
```
