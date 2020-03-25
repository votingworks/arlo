
deps:
	sudo apt install python3.7 python3-pip nodejs libpython3.7-dev libpq-dev
	python3.7 -m pip install pipenv
	sudo npm install -g yarn
	sudo apt install postgresql

# this should only be used for development
initdevdb:
	sudo -u postgres psql -c "create user arlo superuser password 'arlo';"
	sudo -u postgres psql -c "create database arlo with owner arlo;"

install:
	python3.7 -m pipenv install
	yarn install
	yarn --cwd arlo-client install
	yarn --cwd arlo-client build

install-development:
	python3.7 -m pipenv install --dev
	yarn install
	yarn --cwd arlo-client install

resettestdb:
	FLASK_ENV=test make resetdb

resetdb:
	python3.7 -m pipenv run python resetdb.py

dev-environment: deps initdevdb install-development resetdb

typecheck:
	python3.7 -m pipenv run mypy .

format-python:
	python3.7 -m pipenv run black .

lint-server:
	find . -name '*.py' | xargs python3.7 -m pipenv run pylint

test-client:
	yarn --cwd arlo-client lint
	yarn --cwd arlo-client test

# To run a specific test: TEST=<test name> make test-server
test-server:
	FLASK_ENV=test python3.7 -m pipenv run python -m pytest -k '${TEST}' --ignore=arlo-client

# Only tests audit_math
test-math:
	FLASK_ENV=test python3.7 -m pipenv run python -m pytest tests/audit_math_tests -k '${TEST}' 


# Only tests utils
test-utils:
	FLASK_ENV=test python3.7 -m pipenv run python -m pytest tests/util_tests -k '${TEST}' 


# Only tests routes
test-routes:
	FLASK_ENV=test python3.7 -m pipenv run python -m pytest tests/routes_tests -k '${TEST}' 
