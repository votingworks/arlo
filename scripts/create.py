from sqlalchemy_utils import database_exists, create_database
from server.database import engine, init_db

if __name__ == "__main__":
    print(f"database: {engine.url}")

    try:
        if not database_exists(engine.url):
            print("creating database…")
            create_database(engine.url)
    except Exception:
        # sometimes, e.g. on Heroku, you can't even test if the database exists cause permissions
        pass

    print("creating tables…")
    init_db()
