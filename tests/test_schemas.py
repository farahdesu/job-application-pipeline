from datetime import date

import pytest
from pydantic import ValidationError

from jobpipe.schemas import ApplicationCreate, Status


def test_defaults():
    app = ApplicationCreate(company="Acme", role="Engineer")

    assert app.status is Status.SAVED
    assert app.job_url is None
    assert app.notes == ""


def test_strips_whitespace_and_blank_optionals_become_none():
    app = ApplicationCreate(company="  Acme ", role="Engineer", job_url="  ", cv_file="")

    assert app.company == "Acme"
    assert app.job_url is None
    assert app.cv_file is None


@pytest.mark.parametrize("field", ["company", "role"])
def test_required_text_cannot_be_blank(field):
    fields = {"company": "Acme", "role": "Engineer", field: "   "}

    with pytest.raises(ValidationError):
        ApplicationCreate(**fields)


def test_rejects_unknown_status():
    with pytest.raises(ValidationError):
        ApplicationCreate(company="Acme", role="Engineer", status="hired")


def test_rejects_malformed_url():
    with pytest.raises(ValidationError):
        ApplicationCreate(company="Acme", role="Engineer", job_url="not a url")


def test_follow_up_cannot_precede_date_applied():
    with pytest.raises(ValidationError, match="Follow-up date"):
        ApplicationCreate(
            company="Acme",
            role="Engineer",
            date_applied=date(2026, 10, 10),
            follow_up_date=date(2026, 10, 9),
        )


def test_follow_up_without_date_applied_is_allowed():
    app = ApplicationCreate(company="Acme", role="Engineer", follow_up_date=date(2026, 10, 9))

    assert app.follow_up_date == date(2026, 10, 9)
