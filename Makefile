deps:
	sudo apt install python3.8 python3-pip libpython3.8-dev libpq-dev graphicsmagick
	curl -fsSL https://deb.nodesource.com/setup_12.x | sudo -E bash -
	sudo apt-get install -y nodejs
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python3.8 -	
	export PATH="${PATH}:${HOME}/.local/bin/"
	sudo npm install -g yarn
	sudo apt install postgresql

# this should only be used for development
initdevdb:
	sudo -u postgres psql -c "create user arlo superuser password 'arlo';"
	sudo -u postgres psql -c "create database arlo with owner arlo;"

install:
	poetry install --no-dev
	yarn install
	yarn --cwd client install
	yarn --cwd client build

install-development:
	poetry install
	yarn install
	yarn --cwd client install

resettestdb:
	FLASK_ENV=test make resetdb

resetdb:
	FLASK_ENV=$${FLASK_ENV:-development} poetry run python -m scripts.resetdb

dev-environment: deps initdevdb install-development resetdb

typecheck-server:
	poetry run mypy server scripts

format-server:
	poetry run black .

lint-server:
	poetry run pylint server scripts

test-client:
	yarn --cwd client lint
	yarn --cwd client test

test-server:
	poetry run pytest -n auto

test-server-coverage:
	poetry run pytest -n auto --cov=.

run-dev:
	./run-dev.sh
