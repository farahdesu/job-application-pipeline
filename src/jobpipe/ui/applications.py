import pandas as pd
import streamlit as st

from jobpipe.schemas import ApplicationRead, ApplicationUpdate, Status
from jobpipe.ui.components import application_form, flash, get_repo, show_flash

# Bumped after edits/deletes so the table drops its stale row selection.
_TABLE_VERSION_KEY = "applications_table_version"


def _to_frame(apps: list[ApplicationRead]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Company": [a.company for a in apps],
            "Role": [a.role for a in apps],
            "Status": [a.status.label for a in apps],
            "Applied": [a.date_applied for a in apps],
            "Follow-up": [a.follow_up_date for a in apps],
            "CV": [a.cv_file for a in apps],
            "Posting": [str(a.job_url) if a.job_url else None for a in apps],
        }
    )


def _reset_selection() -> None:
    st.session_state[_TABLE_VERSION_KEY] = st.session_state.get(_TABLE_VERSION_KEY, 0) + 1


@st.dialog("Delete application?")
def _confirm_delete(app: ApplicationRead) -> None:
    st.write(f"Permanently delete **{app.role}** at **{app.company}**? This can't be undone.")
    col1, col2 = st.columns(2)
    if col1.button("Delete", type="primary", width="stretch"):
        get_repo().delete(app.id)
        flash(f"Deleted {app.role} at {app.company}")
        _reset_selection()
        st.rerun()
    if col2.button("Cancel", width="stretch"):
        st.rerun()


def _edit_section(app: ApplicationRead) -> None:
    header, delete_col = st.columns([5, 1], vertical_alignment="bottom")
    header.subheader(f"{app.role} — {app.company}")
    if delete_col.button("Delete", icon=":material/delete:", width="stretch"):
        _confirm_delete(app)

    data = application_form(key=f"edit-form-{app.id}", initial=app)
    if data is not None:
        get_repo().update(app.id, ApplicationUpdate.model_validate(data.model_dump()))
        flash(f"Saved {data.role} at {data.company}")
        _reset_selection()
        st.rerun()


def render() -> None:
    show_flash()
    st.title("Applications")

    col1, col2 = st.columns([2, 3])
    statuses = col1.multiselect(
        "Status", list(Status), format_func=lambda s: s.label, placeholder="All statuses"
    )
    search = col2.text_input("Search company or role", placeholder="e.g. Stripe, engineer")

    apps = get_repo().list_applications(statuses=statuses, search=search)
    if not apps:
        st.info("No applications match." if statuses or search else "No applications yet.")
        return

    st.caption(f"{len(apps)} application(s). Select a row to edit or delete it.")
    event = st.dataframe(
        _to_frame(apps),
        key=f"applications-table-{st.session_state.get(_TABLE_VERSION_KEY, 0)}",
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Applied": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Follow-up": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Posting": st.column_config.LinkColumn(display_text="Open"),
        },
    )

    selected = event.selection.rows
    if selected and selected[0] < len(apps):
        st.divider()
        _edit_section(apps[selected[0]])
