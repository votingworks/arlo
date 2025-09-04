## Prepare environment for development

prepare:
	sudo apt update
	# Install python with virtual env and dev extensions, graphicsmagick, and gcc
	sudo apt install -y python3.9 python3.9-venv libpython3.9-dev python-dev libpq-dev graphicsmagick gcc postgresql
	# Install node: https://github.com/nodesource/distributions/blob/master/README.md#deb		
	curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
	sudo apt-get install -y nodejs
	# Install poetry: https://python-poetry.org/docs/#installing-with-the-official-installer
	curl -sSL https://install.python-poetry.org | python3.9 -
	# Install yarn
	sudo npm install -g yarn
	yarn install
	yarn prepare # Sets up Git hooks
	# Ensure poetry can be called from the command line and make commands
	@echo "User action required: Make poetry available in your PATH. This will vary depending on your configuration"
	@echo "If using bash, add 'export PATH=\"\$$PATH:\$$HOME/.local/bin\"' to your .bashrc and then run 'source ~/.bashrc'"

db-prepare:
	sudo systemctl start postgresql
	sudo -u postgres psql -c "create user arlo superuser password 'arlo';"
	sudo -u postgres psql -c "create database arlo with owner arlo;"
	make db-clean

## Local development

dev-environment: prepare db-prepare install 

run: # Used for development, not during production deployment. Defaults to 3 ports - 8080, 3000, 3001
	./run-dev.sh

## Following commands are mainly for server development, since client is encapsulated in a subdirectory

install:
	poetry install
	yarn install
	make -C client install

typecheck:
	poetry run basedpyright --baseline-file .basedpyright/baseline.json

format:
	poetry run ruff format .

lint:
	poetry run ruff check server scripts fixtures

test:
	poetry run pytest -n auto --ignore=server/tests/arlo-extra-tests 

test-clean:
	FLASK_ENV=test make db-clean

test-coverage:
	poetry run pytest -n auto --cov=. --ignore=server/tests/arlo-extra-tests

test-extra: # This runs the _extra files_ repo tests as well (must download first)
	poetry run pytest -n auto 

test-extra-coverage:
	poetry run pytest -n auto --cov=.

## Database

db-clean:
	FLASK_ENV=$${FLASK_ENV:-development} poetry run python -m scripts.resetdb

db-migrate:
	FLASK_ENV=$${FLASK_ENV:-development} poetry run alembic upgrade head
