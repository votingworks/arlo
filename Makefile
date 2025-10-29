SHELL := /bin/bash

#
# Dev setup
#

dev-environment:
	@echo '⚠️  This command assumes an Ubuntu 24 environment'
	@echo

	@# Necessary for Python 3.11 package discovery
	sudo add-apt-repository -y ppa:deadsnakes/ppa

	sudo apt update

	sudo apt install -y curl

	@# Install Python 3.11
	sudo apt install -y python3.11 python3.11-venv libpython3.11-dev python-dev-is-python3

	@# Install other apt packages
	sudo apt install -y gcc graphicsmagick libpq-dev postgresql

	@# Install Node: https://github.com/nodesource/distributions/blob/master/README.md#deb
	curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
	sudo apt install -y nodejs

	@# Install Poetry: https://python-poetry.org/docs/#installing-with-the-official-installer
	curl -sSL https://install.python-poetry.org | python3.11 -

	@# Install Yarn
	sudo npm install -g yarn
	yarn install
	yarn prepare # Set up Git hooks

	@echo
	@echo '⚠️  User action required: Make poetry available in your PATH.'
	@echo '⚠️  If using bash, run `export PATH="$$PATH:$$HOME/.local/bin" >> ~/.bashrc && source ~/.bashrc`'

install:
	poetry env use 3.11
	poetry install
	make -C client install

dev-dbs:
	sudo systemctl start postgresql
	sudo -u postgres psql -c "create user arlo superuser password 'arlo';" || \
		sudo -u postgres psql -c "alter user arlo superuser password 'arlo';"

	@# The following commands require Python packages to be installed
	make db-clean # Initialize dev DB
	FLASK_ENV=test make db-clean # Initialize test DB

	sudo -u postgres psql -c "alter system set timezone = 'UTC'";
	sudo systemctl restart postgresql

run: # Used for development, not during production deployment. Defaults to 3 ports - 8080, 3000, 3001
	./run-dev.sh

#
# Server-specific commands; see client/Makefile for client-specific commands
#

typecheck:
	poetry run basedpyright --baseline-file .basedpyright/baseline.json

format:
	poetry run ruff format .

lint:
	poetry run ruff check server scripts fixtures

test:
	poetry run pytest -n auto --ignore=server/tests/arlo-extra-tests 

test-coverage:
	poetry run pytest -n auto --cov=. --ignore=server/tests/arlo-extra-tests

test-extra: # This runs the tests in the arlo-extra-tests as well (must download first)
	poetry run pytest -n auto

test-extra-coverage:
	poetry run pytest -n auto --cov=.

db-clean:
	FLASK_ENV=$${FLASK_ENV:-development} poetry run python -m scripts.resetdb

db-migrate:
	FLASK_ENV=$${FLASK_ENV:-development} poetry run alembic upgrade head
