# Set path so we can find poetry after install
PATH := $(PATH):$(HOME)/.local/bin

deps:
	sudo apt update
	sudo apt install -y python3.9 python3.9-venv libpython3.9-dev libpq-dev graphicsmagick
	# Install node: https://github.com/nodesource/distributions/blob/master/README.md#deb		
	curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
	sudo apt-get install -y nodejs
	# Install poetry: https://python-poetry.org/docs/#installing-with-the-official-installer
	curl -sSL https://install.python-poetry.org | python3.9 -
	sudo npm install -g yarn
	sudo apt install -y postgresql
	sudo systemctl start postgresql

# this should only be used for development
initdevdb:
	sudo -u postgres psql -c "create user arlo superuser password 'arlo';"
	sudo -u postgres psql -c "create database arlo with owner arlo;"

install-development:
	poetry install
	yarn install
	yarn --cwd client install

setup-git-hooks:
	yarn prepare

resettestdb:
	FLASK_ENV=test make resetdb

resetdb:
	FLASK_ENV=$${FLASK_ENV:-development} poetry run python -m scripts.resetdb

dev-environment: deps initdevdb install-development setup-git-hooks resetdb

typecheck-server:
	poetry run mypy server scripts fixtures

format-server:
	poetry run black .

lint-server:
	poetry run pylint server scripts fixtures

test-client:
	yarn --cwd client lint
	yarn --cwd client test

test-server:
	poetry run pytest -n auto --ignore=server/tests/arlo-extra-tests

test-server-coverage:
	poetry run pytest -n auto --cov=. --ignore=server/tests/arlo-extra-tests

# This runs all tests. If you have the extra files repo included, it runs those as well.
test-server-extra: 
	poetry run pytest -n auto 

test-server-extra-coverage:
	poetry run pytest -n auto --cov=. 


run-dev:
	./run-dev.sh
