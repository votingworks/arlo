import sys, os
from sqlalchemy_utils import database_exists, create_database, drop_database
from alembic.config import Config
from alembic import command
from server.database import engine, reset_db

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

    print("resetting tables…")
    reset_db()

    print("stamping latest migration revision...")
    # Following recipe: https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))
    command.stamp(alembic_cfg, "head")
