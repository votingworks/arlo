
install:
	pipenv install
	yarn --cwd arlo-client install
	yarn --cwd arlo-client build

resetdb-sqlite:
	rm -f arlo.db
	DATABASE_URL="" pipenv run python create.py

resetdb-postgres:
	dropdb arlo
	createdb arlo
	pipenv run python create.py

typecheck:
	pipenv run mypy .

test-client:
	yarn --cwd arlo-client test

test-server:
	pipenv run python -m pytest --ignore=arlo-client
