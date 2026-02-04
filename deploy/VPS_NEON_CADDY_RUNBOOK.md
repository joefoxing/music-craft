# VPS + Neon + Caddy Deployment Runbook

## Overview
This project is deployed on a VPS using:
- **Gunicorn** for serving the Flask app
- **systemd** to keep the app running
- **Caddy** as the reverse proxy + TLS
- **Neon Postgres** for the database

## 1) VPS directory layout
Recommended:
- `/opt/lyric_cover` (your app checkout)
- `/etc/lyric_cover.env` (secrets and env vars; not in git)

## 2) Create app user (optional)
You can run as `www-data` (default in the provided unit) or create a dedicated user.

## 3) Install system packages
You need Python, venv, and Caddy.

## 4) Create venv + install deps
From `/opt/lyric_cover`:
- `python3 -m venv .venv`
- `. .venv/bin/activate`
- `pip install -r requirements.txt`

## 5) Configure Neon
In Neon, copy the connection string and ensure SSL is required.

Example `DATABASE_URL`:
- `postgresql://USER:PASSWORD@HOST/DB?sslmode=require`

## 6) Create `/etc/lyric_cover.env`
Example (fill values):
- `DATABASE_URL=postgresql://...?...sslmode=require`
- `AUTO_CREATE_DB=false`
- `SECRET_KEY=...`
- `KIE_API_KEY=...`
- `MAIL_SERVER=...`
- `MAIL_USERNAME=...`
- `MAIL_PASSWORD=...`
- `MAIL_DEFAULT_SENDER=...`
- `OAUTH_ENABLED=false`
- `GOOGLE_OAUTH_CLIENT_ID=`
- `GOOGLE_OAUTH_CLIENT_SECRET=`
- `GITHUB_OAUTH_CLIENT_ID=`
- `GITHUB_OAUTH_CLIENT_SECRET=`

## 7) Run DB migrations
From `/opt/lyric_cover` (with env loaded):
- `alembic upgrade head`

If you have not created the initial migration yet, do:
- `alembic revision --autogenerate -m "baseline"`
- `alembic upgrade head`

## 8) Install systemd service
Copy `deploy/systemd/lyric_cover.service` to:
- `/etc/systemd/system/lyric_cover.service`

Then:
- `systemctl daemon-reload`
- `systemctl enable --now lyric_cover`
- `systemctl status lyric_cover`

## 9) Configure Caddy
Copy `deploy/caddy/Caddyfile` to:
- `/etc/caddy/Caddyfile`

Replace:
- `admin@joefoxing.com` (or your preferred ACME notification email)
- `joefoxing.com`

Then:
- `systemctl reload caddy`

## 10) Smoke test
- `curl -I https://your-domain.com/`

## Notes
- This project expects **Caddy** to terminate TLS and reverse proxy to Gunicorn on `127.0.0.1:8000`.
- Keep `AUTO_CREATE_DB=false` in production so schema changes happen through Alembic.
