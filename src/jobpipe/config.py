"""Runtime configuration, read from environment variables with sensible defaults."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "jobpipe.db"


def db_url() -> str:
    """SQLAlchemy URL for the app database. Override the file with JOBPIPE_DB_PATH."""
    path = Path(os.environ.get("JOBPIPE_DB_PATH", DEFAULT_DB_PATH))
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"
