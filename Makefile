PYTHON ?= python
PIP ?= pip

ifneq (,$(wildcard .env))
include .env
export $(shell sed -n 's/^\([A-Za-z0-9_]\+\)=.*/\1/p' .env)
endif

.PHONY: install-dev migrate test test-docker

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

migrate:
	PYTHONPATH=$(PYTHONPATH):$(PWD) python -m app.tools.pre_migration_cleanup || true
	PYTHONPATH=$(PYTHONPATH):$(PWD) alembic upgrade head

test: install-dev
	pytest

# Run tests inside the Docker container (uses python 3.11 in the image)
test-docker:
	docker compose -f docker-compose.local.yml up -d db
	docker compose -f docker-compose.local.yml build api
	docker compose -f docker-compose.local.yml run --rm --user root \
	  -v $(PWD):/app \
	  -e PYTHONPATH=/app \
	  -e DATABASE_USE=$(DATABASE_USE) \
	  -e DATABASE_URL_TEST=$(DATABASE_URL_TEST) \
	  -e ALEMBIC_RUN_SYNC=1 \
	  -e DISABLE_STARTUP_SEED=1 \
	  -e DISABLE_STARTUP_MIGRATIONS=1 \
	  api sh -lc "pip install -r requirements-dev.txt && pytest -q"
