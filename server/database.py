import re
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker, Query
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from .config import DATABASE_URL

# Based on https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/#declarative

engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))

meta = MetaData(
    naming_convention={
        "ix": "%(column_0_N_label)s_idx",
        "uq": "%(table_name)s_%(column_0_N_name)s_key",
        "ck": "%(table_name)s_%(constraint_name)s_check",
        "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
        "pk": "%(table_name)s_pkey",
    }
)


@as_declarative(metadata=meta)
class Base:
    query: Query = db_session.query_property()

    # pylint: disable=no-self-argument,no-member
    @declared_attr
    def __tablename__(cls):
        # Convert CamelCase model name to snake_case table name
        # https://stackoverflow.com/a/1176023
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()


def init_db(engine=engine):
    # pylint: disable=wildcard-import,import-outside-toplevel,unused-import
    import server.models

    Base.metadata.create_all(bind=engine)


def reset_db():
    # pylint: disable=wildcard-import,import-outside-toplevel,unused-import
    import server.models

    Base.metadata.drop_all(bind=engine)
    init_db()


def clear_db():  # pragma: no cover
    # pylint: disable=wildcard-import,import-outside-toplevel,unused-import
    import server.models

    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete())
