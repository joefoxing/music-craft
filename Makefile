.PHONY: up down logs reset build shell

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
