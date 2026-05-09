.PHONY: help up down build logs shell-backend shell-db migrate seed reset lint fmt test

help: ## Show this help
	@grep -E '^[a-zA-Z_/-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

cp-env: ## Copy .env.example → .env if not present
	@test -f .env || cp .env.example .env && echo "Created .env from .env.example"

up: cp-env ## Start all services
	docker compose up -d

up-logs: cp-env ## Start all services and follow logs
	docker compose up

down: ## Stop all services
	docker compose down

build: cp-env ## Rebuild all images
	docker compose build --no-cache

logs: ## Tail logs from all containers
	docker compose logs -f

logs-backend: ## Tail backend logs
	docker compose logs -f backend

logs-worker: ## Tail worker logs
	docker compose logs -f worker

shell-backend: ## Open shell in backend container
	docker compose exec backend bash

shell-db: ## Open psql in database
	docker compose exec postgres psql -U stock_intel stock_intel

migrate: ## Run Alembic migrations
	docker compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add table")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed database with mock data
	docker compose exec backend python scripts/seed.py

reset: ## Destroy and recreate everything (⚠ data loss!)
	docker compose down -v
	docker compose up -d
	sleep 5
	docker compose exec backend alembic upgrade head
	docker compose exec backend python scripts/seed.py

fmt-backend: ## Format Python code
	docker compose exec backend black app/ && isort app/

lint-backend: ## Lint Python code
	docker compose exec backend flake8 app/ --max-line-length=120

test-backend: ## Run backend tests
	docker compose exec backend pytest tests/ -v

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

fmt-frontend: ## Format frontend code
	cd frontend && npm run lint:fix
