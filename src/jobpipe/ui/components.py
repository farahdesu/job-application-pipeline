"""Shared Streamlit helpers: repository access, flash messages, the application form."""

import streamlit as st
from pydantic import ValidationError

from jobpipe.db import init_db, make_engine, make_session_factory
from jobpipe.repository import ApplicationRepository
from jobpipe.schemas import ApplicationCreate, ApplicationRead, Status

_FLASH_KEY = "_flash"


@st.cache_resource
def get_repo() -> ApplicationRepository:
    engine = make_engine()
    init_db(engine)
    return ApplicationRepository(make_session_factory(engine))


def flash(message: str) -> None:
    """Queue a toast to show after the next rerun."""
    st.session_state[_FLASH_KEY] = message


def show_flash() -> None:
    if message := st.session_state.pop(_FLASH_KEY, None):
        st.toast(message, icon=":material/check_circle:")


def show_validation_errors(error: ValidationError) -> None:
    for err in error.errors():
        field = ".".join(str(part) for part in err["loc"]).replace("_", " ")
        message = err["msg"].removeprefix("Value error, ")
        st.error(f"**{field.capitalize()}**: {message}" if field else message)


def application_form(key: str, initial: ApplicationRead | None = None) -> ApplicationCreate | None:
    """Render the add/edit form. Returns validated data on a successful submit, else None."""
    statuses = list(Status)
    with st.form(key):
        col1, col2 = st.columns(2)
        company = col1.text_input("Company *", value=initial.company if initial else "")
        role = col2.text_input("Role *", value=initial.role if initial else "")
        job_url = st.text_input(
            "Job posting URL",
            value=str(initial.job_url) if initial and initial.job_url else "",
            placeholder="https://",
        )

        col1, col2, col3 = st.columns(3)
        status = col1.selectbox(
            "Status",
            statuses,
            index=statuses.index(initial.status) if initial else 0,
            format_func=lambda s: s.label,
        )
        date_applied = col2.date_input(
            "Date applied", value=initial.date_applied if initial else None, format="YYYY-MM-DD"
        )
        follow_up_date = col3.date_input(
            "Follow-up date", value=initial.follow_up_date if initial else None, format="YYYY-MM-DD"
        )

        cv_file = st.text_input(
            "CV file used",
            value=(initial.cv_file or "") if initial else "",
            placeholder="e.g. cv_backend_v3.pdf",
        )
        job_description = st.text_area(
            "Job description", value=initial.job_description if initial else "", height=250
        )
        notes = st.text_area("Notes", value=initial.notes if initial else "", height=100)

        submitted = st.form_submit_button("Save", type="primary")

    if not submitted:
        return None
    try:
        return ApplicationCreate(
            company=company,
            role=role,
            job_url=job_url,
            date_applied=date_applied,
            job_description=job_description,
            status=status,
            cv_file=cv_file,
            notes=notes,
            follow_up_date=follow_up_date,
        )
    except ValidationError as error:
        show_validation_errors(error)
        return None
