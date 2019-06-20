
install:
	pipenv install

resetdb-sqlite:
	rm -f arlo.db
	DATABASE_URL="" pipenv run python create.py

resetdb-postgres:
	dropdb arlo
	createdb arlo
	pipenv run python create.py

test-client:
	yarn --cwd arlo-client test

test-server:
	pipenv run python -m pytest --ignore=arlo-client
