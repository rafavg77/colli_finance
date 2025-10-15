PYTHON ?= python
PIP ?= pip

.PHONY: install-dev test test-docker

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

test: install-dev
	pytest

# Run tests inside the Docker container (uses python 3.11 in the image)
test-docker:
	docker compose -f docker-compose.local.yml up -d db
	docker compose -f docker-compose.local.yml build api
	docker compose -f docker-compose.local.yml run --rm --user root \
	  -v $(PWD):/app \
	  -e PYTHONPATH=/app \
	  -e DATABASE_USE=dev \
	  -e DATABASE_URL_TEST=postgresql+asyncpg://colli:colli@db:5432/colli_finance_test \
	  -e ALEMBIC_RUN_SYNC=1 \
	  -e DISABLE_STARTUP_SEED=1 \
	  -e DISABLE_STARTUP_MIGRATIONS=1 \
	  api sh -lc "pip install -r requirements-dev.txt && pytest -q"
