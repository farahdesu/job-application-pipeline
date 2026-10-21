"""Engine, session factory and schema creation."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from jobpipe import config


class Base(DeclarativeBase):
    pass


def make_engine(url: str | None = None) -> Engine:
    return create_engine(url or config.db_url())


def init_db(engine: Engine) -> None:
    """Create any missing tables. Does not alter existing ones (no migrations yet)."""
    from jobpipe import models  # noqa: F401  (registers tables on Base.metadata)

    Base.metadata.create_all(engine)


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(engine, expire_on_commit=False)
