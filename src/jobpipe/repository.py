"""All database access goes through ApplicationRepository.

Methods accept and return Pydantic schemas, never ORM objects, so callers
(the UI, future AI modules) stay independent of SQLAlchemy.
"""

from collections.abc import Iterable
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from jobpipe.models import Application
from jobpipe.schemas import (
    CLOSED_STATUSES,
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    Status,
)


class ApplicationNotFoundError(LookupError):
    pass


def _to_columns(data: ApplicationCreate) -> dict:
    values = data.model_dump()
    values["job_url"] = str(data.job_url) if data.job_url else None
    values["status"] = data.status.value
    return values


def _escape_like(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ApplicationRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, data: ApplicationCreate) -> ApplicationRead:
        with self._session_factory.begin() as session:
            row = Application(**_to_columns(data))
            session.add(row)
            session.flush()
            return ApplicationRead.model_validate(row)

    def get(self, app_id: int) -> ApplicationRead | None:
        with self._session_factory() as session:
            row = session.get(Application, app_id)
            return ApplicationRead.model_validate(row) if row else None

    def update(self, app_id: int, changes: ApplicationUpdate) -> ApplicationRead:
        with self._session_factory.begin() as session:
            row = session.get(Application, app_id)
            if row is None:
                raise ApplicationNotFoundError(app_id)
            current = ApplicationRead.model_validate(row).model_dump(
                exclude={"id", "created_at", "updated_at"}
            )
            merged = ApplicationCreate.model_validate(
                current | changes.model_dump(exclude_unset=True)
            )
            for column, value in _to_columns(merged).items():
                setattr(row, column, value)
            session.flush()
            return ApplicationRead.model_validate(row)

    def delete(self, app_id: int) -> bool:
        """Delete an application. Returns False if it did not exist."""
        with self._session_factory.begin() as session:
            row = session.get(Application, app_id)
            if row is None:
                return False
            session.delete(row)
            return True

    def list_applications(
        self,
        statuses: Iterable[Status] | None = None,
        search: str | None = None,
    ) -> list[ApplicationRead]:
        """List applications, newest first.

        `statuses`: keep only these (None or empty = all).
        `search`: case-insensitive substring match on company or role.
        """
        query = select(Application)
        status_values = [Status(s).value for s in statuses or []]
        if status_values:
            query = query.where(Application.status.in_(status_values))
        if search and search.strip():
            pattern = f"%{_escape_like(search.strip())}%"
            query = query.where(
                Application.company.ilike(pattern, escape="\\")
                | Application.role.ilike(pattern, escape="\\")
            )
        query = query.order_by(
            Application.date_applied.desc().nulls_last(),
            Application.created_at.desc(),
        )
        with self._session_factory() as session:
            return [ApplicationRead.model_validate(r) for r in session.scalars(query)]

    def counts_by_status(self) -> dict[Status, int]:
        """Count per status, including statuses with zero applications."""
        query = select(Application.status, func.count()).group_by(Application.status)
        with self._session_factory() as session:
            found = dict(session.execute(query).all())
        return {status: found.get(status.value, 0) for status in Status}

    def needs_follow_up(self, today: date | None = None) -> list[ApplicationRead]:
        """Open applications whose follow-up date is today or earlier, oldest first."""
        today = today or date.today()
        query = (
            select(Application)
            .where(Application.follow_up_date.is_not(None))
            .where(Application.follow_up_date <= today)
            .where(Application.status.not_in([s.value for s in CLOSED_STATUSES]))
            .order_by(Application.follow_up_date)
        )
        with self._session_factory() as session:
            return [ApplicationRead.model_validate(r) for r in session.scalars(query)]
