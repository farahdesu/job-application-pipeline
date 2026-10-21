"""SQLAlchemy ORM models. Only the repository layer should import these."""

from datetime import UTC, date, datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from jobpipe.db import Base


def _utcnow() -> datetime:
    # SQLite drops tzinfo, so store naive UTC consistently.
    return datetime.now(UTC).replace(tzinfo=None)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200), index=True)
    role: Mapped[str] = mapped_column(String(200))
    job_url: Mapped[str | None] = mapped_column(String(2000))
    date_applied: Mapped[date | None]
    job_description: Mapped[str] = mapped_column(Text, default="")
    # Stored as plain text (not a DB enum) so new statuses don't need a migration;
    # validity is enforced by schemas.Status.
    status: Mapped[str] = mapped_column(String(20), index=True)
    cv_file: Mapped[str | None] = mapped_column(String(500))
    notes: Mapped[str] = mapped_column(Text, default="")
    follow_up_date: Mapped[date | None] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=_utcnow, onupdate=_utcnow)
