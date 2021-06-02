deps:
	sudo apt install python3.8 python3-pip nodejs libpython3.8-dev libpq-dev graphicsmagick
	python3.8 -m pip install pipenv
	sudo npm install -g yarn
	sudo apt install postgresql

# this should only be used for development
initdevdb:
	sudo -u postgres psql -c "create user arlo superuser password 'arlo';"
	sudo -u postgres psql -c "create database arlo with owner arlo;"

install:
	pipenv install
	yarn install
	yarn --cwd client install
	yarn --cwd client build

install-development:
	pipenv install --dev
	yarn install
	yarn --cwd client install

resettestdb:
	FLASK_ENV=test make resetdb

resetdb:
	FLASK_ENV=$${FLASK_ENV:-development} pipenv run python -m scripts.resetdb

dev-environment: deps initdevdb install-development resetdb

typecheck-server:
	pipenv run mypy server scripts

format-server:
	pipenv run black .

lint-server:
	pipenv run pylint server scripts

test-client:
	yarn --cwd client lint
	yarn --cwd client test

test-server:
	pipenv run pytest -n auto

test-server-coverage:
	pipenv run pytest -n auto --cov=.

run-dev:
	./run-dev.sh
