"""Pydantic schemas: the data contract between the repository, the UI and future modules."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class Status(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"

    @property
    def label(self) -> str:
        return self.value.capitalize()


# Applications in these states never show up as needing follow-up.
CLOSED_STATUSES = frozenset({Status.OFFER, Status.REJECTED, Status.GHOSTED})


def _blank_to_none(value: object) -> object:
    if isinstance(value, str) and not value.strip():
        return None
    return value


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    job_url: HttpUrl | None = None
    date_applied: date | None = None
    job_description: str = ""
    status: Status = Status.SAVED
    cv_file: str | None = Field(default=None, max_length=500)
    notes: str = ""
    follow_up_date: date | None = None

    @field_validator("job_url", "cv_file", mode="before")
    @classmethod
    def _optional_text(cls, value: object) -> object:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def _follow_up_not_before_applied(self) -> "ApplicationCreate":
        if self.date_applied and self.follow_up_date and self.follow_up_date < self.date_applied:
            raise ValueError("Follow-up date cannot be before the date applied")
        return self


class ApplicationUpdate(BaseModel):
    """Partial update: only fields that are explicitly set are changed.

    The merged record is re-validated as an ApplicationCreate by the repository,
    so cross-field rules still apply.
    """

    company: str | None = None
    role: str | None = None
    job_url: HttpUrl | str | None = None
    date_applied: date | None = None
    job_description: str | None = None
    status: Status | None = None
    cv_file: str | None = None
    notes: str | None = None
    follow_up_date: date | None = None


class ApplicationRead(ApplicationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
