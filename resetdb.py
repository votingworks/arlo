import sys

from arlo_server.routes import init_db
from config import DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database, drop_database

if __name__ == "__main__":
    skip_db_creation = len(sys.argv) > 1 and sys.argv[1] == "--skip-db-creation"
    skip_table_creation = len(sys.argv) > 1 and sys.argv[1] == "--skip-table-creation"

    engine = create_engine(DATABASE_URL)
    print(f"database: {engine.url}")

    if skip_db_creation:
        print("skipping DB drop/create ...")
    else:
        if database_exists(engine.url):
            print("dropping database…")
            drop_database(engine.url)

        print("creating database…")
        create_database(engine.url)

    if skip_table_creation:
        print("skipping creating tables ...")
    else:
        print("creating tables…")
        init_db()
