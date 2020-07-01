import sys
from sqlalchemy_utils import database_exists, create_database, drop_database
from server.database import engine, init_db

if __name__ == "__main__":
    # a simple flag to skip DB creation
    skip_db_creation = len(sys.argv) > 1 and sys.argv[1] == "--skip-db-creation"

    print(f"database: {engine.url}")

    if skip_db_creation:
        print("skipping DB drop/create ...")
    else:
        if database_exists(engine.url):
            print("dropping database…")
            drop_database(engine.url)

        print("creating database…")
        create_database(engine.url)

    print("creating tables…")
    init_db()
