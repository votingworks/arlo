from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Query
from sqlalchemy.ext.declarative import declarative_base, as_declarative
from .config import DATABASE_URL

# Based on https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/#declarative

engine = create_engine(DATABASE_URL)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


@as_declarative()
class Base:
    query: Query = db_session.query_property()


def init_db():
    from .models import *  # pylint: disable=wildcard-import,import-outside-toplevel,unused-import

    Base.metadata.create_all(bind=engine)
