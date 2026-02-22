.PHONY: up down logs reset build shell test test-e2e install-e2e

up:
	@if not exist .env copy .env.example .env
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

build:
	docker compose build

reset:
	docker compose down -v
	docker compose up --build -d

shell:
	docker compose exec app /bin/bash
# ── Testing ────────────────────────────────────────────────────────────────

install-e2e:
	pip install -r requirements-e2e.txt
	playwright install chromium

test:
	pytest tests/ -v

test-e2e:
	pytest tests/e2e/ --browser chromium -v

test-e2e-headed:
	pytest tests/e2e/ --browser chromium --headed -v