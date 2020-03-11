
deps:
	sudo apt install python3.7 python3-pip nodejs libpython3.7-dev libpq-dev
	python3 -m pip install pipenv
	sudo npm install -g yarn
	sudo apt install postgresql

# this should only be used for development
initdevdb:
	sudo -u postgres psql -c "create user arlo superuser password 'arlo';"
	sudo -u postgres psql -c "create database arlo with owner arlo;"

install:
	python3 -m pipenv install
	yarn install
	yarn --cwd arlo-client install
	yarn --cwd arlo-client build

install-development:
	python3 -m pipenv install --dev
	yarn install
	yarn --cwd arlo-client install

resettestdb:
	FLASK_ENV=test make resetdb

resetdb:
	python3 -m pipenv run python resetdb.py

dev-environment: deps initdevdb install-development resetdb

typecheck:
	python3 -m pipenv run mypy .

format-python:
	python3 -m pipenv run black .

test-client:
	yarn --cwd arlo-client lint
	yarn --cwd arlo-client test

# To run a specific test: TEST=<test name> make test-server
test-server:
	FLASK_ENV=test python3 -m pipenv run python -m pytest -k '${TEST}' --ignore=arlo-client
