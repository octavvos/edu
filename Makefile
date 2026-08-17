.PHONY: up down migrate seed test lint fmt logs shell

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec backend python manage.py migrate

seed:
	docker compose exec backend python manage.py seed_rbac

test:
	docker compose exec backend pytest --cov=apps --cov-report=term-missing

lint:
	docker compose exec backend ruff check .
	docker compose exec backend mypy apps config libs

fmt:
	docker compose exec backend ruff check --fix .

logs:
	docker compose logs -f backend celery-worker celery-beat

shell:
	docker compose exec backend python manage.py shell
