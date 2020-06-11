from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from server.app import db
from server.config import DATABASE_URL

if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)
    print(f"database: {engine.url}")

    try:
        if not database_exists(engine.url):
            print("creating database…")
            create_database(engine.url)
    except Exception:
        # sometimes, e.g. on Heroku, you can't even test if the database exists cause permissions
        pass

    print("creating tables…")
    db.create_all()
