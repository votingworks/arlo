import re
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Query
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from .config import DATABASE_URL

# Based on https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/#declarative

engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))


@as_declarative()
class Base:
    query: Query = db_session.query_property()
    # pylint: disable=no-self-argument,no-member
    @declared_attr
    def __tablename__(cls):
        # Convert CamelCase model name to snake_case table name
        # https://stackoverflow.com/a/1176023
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()


def init_db():
    # pylint: disable=wildcard-import,import-outside-toplevel,unused-import
    import server.models

    Base.metadata.create_all(bind=engine)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
