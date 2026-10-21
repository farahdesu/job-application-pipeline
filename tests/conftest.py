import pytest

from jobpipe.db import init_db, make_engine, make_session_factory
from jobpipe.repository import ApplicationRepository
from jobpipe.schemas import ApplicationCreate


@pytest.fixture
def repo(tmp_path):
    """A repository backed by a fresh SQLite file per test."""
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    init_db(engine)
    yield ApplicationRepository(make_session_factory(engine))
    engine.dispose()


@pytest.fixture
def add(repo):
    """Create an application with sensible defaults; override any field via kwargs."""

    def _add(**overrides):
        fields = {"company": "Acme", "role": "Backend Engineer"} | overrides
        return repo.create(ApplicationCreate(**fields))

    return _add
