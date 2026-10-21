from datetime import date, timedelta

import pytest

from jobpipe.repository import ApplicationNotFoundError
from jobpipe.schemas import ApplicationCreate, ApplicationUpdate, Status

TODAY = date(2026, 10, 21)


def test_create_and_get_round_trips_all_fields(repo):
    data = ApplicationCreate(
        company="Acme",
        role="Data Engineer",
        job_url="https://jobs.acme.com/123",
        date_applied=date(2026, 10, 1),
        job_description="Build pipelines.\nPython, SQL.",
        status=Status.APPLIED,
        cv_file="cv_data_eng_v2.pdf",
        notes="Referral from Sam",
        follow_up_date=date(2026, 10, 15),
    )

    created = repo.create(data)
    fetched = repo.get(created.id)

    assert fetched == created
    assert fetched.model_dump(exclude={"id", "created_at", "updated_at"}) == data.model_dump()
    assert fetched.created_at is not None


def test_get_missing_returns_none(repo):
    assert repo.get(999) is None


def test_update_changes_only_given_fields_and_bumps_updated_at(repo, add):
    original = add(status=Status.APPLIED, notes="first")

    updated = repo.update(original.id, ApplicationUpdate(status=Status.INTERVIEW))

    assert updated.status is Status.INTERVIEW
    assert updated.notes == "first"
    assert updated.updated_at > original.updated_at
    assert repo.get(original.id).status is Status.INTERVIEW


def test_update_can_clear_optional_field(repo, add):
    original = add(follow_up_date=TODAY)

    updated = repo.update(original.id, ApplicationUpdate(follow_up_date=None))

    assert updated.follow_up_date is None


def test_update_revalidates_merged_record(repo, add):
    original = add(date_applied=date(2026, 10, 10))

    with pytest.raises(ValueError, match="Follow-up date"):
        repo.update(original.id, ApplicationUpdate(follow_up_date=date(2026, 10, 1)))

    assert repo.get(original.id).follow_up_date is None


def test_update_missing_raises(repo):
    with pytest.raises(ApplicationNotFoundError):
        repo.update(999, ApplicationUpdate(notes="x"))


def test_delete(repo, add):
    app = add()

    assert repo.delete(app.id) is True
    assert repo.get(app.id) is None
    assert repo.delete(app.id) is False


def test_list_filters_by_status(repo, add):
    add(company="A", status=Status.APPLIED)
    add(company="B", status=Status.INTERVIEW)
    add(company="C", status=Status.REJECTED)

    result = repo.list_applications(statuses=[Status.APPLIED, Status.INTERVIEW])

    assert {a.company for a in result} == {"A", "B"}
    assert len(repo.list_applications()) == 3
    assert len(repo.list_applications(statuses=[])) == 3


def test_list_search_is_case_insensitive_partial_on_company_or_role(repo, add):
    add(company="Stripe", role="Platform Engineer")
    add(company="Acme", role="Data Engineer")
    add(company="Globex", role="Product Manager")

    assert {a.company for a in repo.list_applications(search="stri")} == {"Stripe"}
    assert {a.company for a in repo.list_applications(search="ENGINEER")} == {"Stripe", "Acme"}
    assert repo.list_applications(search="nomatch") == []


def test_list_search_treats_wildcards_literally(repo, add):
    add(company="100% Remote Co")
    add(company="Other")

    assert {a.company for a in repo.list_applications(search="%")} == {"100% Remote Co"}


def test_list_combines_status_filter_and_search(repo, add):
    add(company="Acme", status=Status.APPLIED)
    add(company="Acme Labs", status=Status.REJECTED)
    add(company="Globex", status=Status.APPLIED)

    result = repo.list_applications(statuses=[Status.APPLIED], search="acme")

    assert [a.company for a in result] == ["Acme"]


def test_list_orders_by_date_applied_desc_with_undated_last(repo, add):
    add(company="old", date_applied=date(2026, 9, 1))
    add(company="undated")
    add(company="new", date_applied=date(2026, 10, 1))

    assert [a.company for a in repo.list_applications()] == ["new", "old", "undated"]


def test_counts_by_status_includes_zeroes(repo, add):
    add(status=Status.APPLIED)
    add(status=Status.APPLIED)
    add(status=Status.OFFER)

    counts = repo.counts_by_status()

    assert counts[Status.APPLIED] == 2
    assert counts[Status.OFFER] == 1
    assert counts[Status.GHOSTED] == 0
    assert set(counts) == set(Status)


def test_needs_follow_up(repo, add):
    add(company="today", status=Status.APPLIED, follow_up_date=TODAY)
    add(company="overdue", status=Status.INTERVIEW, follow_up_date=TODAY - timedelta(days=3))
    add(company="future", status=Status.APPLIED, follow_up_date=TODAY + timedelta(days=1))
    add(company="no date", status=Status.APPLIED)
    add(company="rejected", status=Status.REJECTED, follow_up_date=TODAY - timedelta(days=1))
    add(company="offer", status=Status.OFFER, follow_up_date=TODAY)
    add(company="ghosted", status=Status.GHOSTED, follow_up_date=TODAY)

    result = repo.needs_follow_up(today=TODAY)

    assert [a.company for a in result] == ["overdue", "today"]
