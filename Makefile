
install:
	pipenv install
	yarn --cwd arlo-client install
	yarn --cwd arlo-client build

install-development:
	pipenv install --dev
	yarn --cwd arlo-client install

resetdb:
	pipenv run python resetdb.py

typecheck:
	pipenv run mypy .

test-client:
	yarn --cwd arlo-client lint
	yarn --cwd arlo-client test

test-server:
	FLASK_ENV=test pipenv run python -m pytest --ignore=arlo-client
