from datetime import date

import pandas as pd
import streamlit as st

from jobpipe.schemas import Status
from jobpipe.ui.components import get_repo, show_flash


def render() -> None:
    show_flash()
    st.title("Dashboard")
    repo = get_repo()

    counts = repo.counts_by_status()
    st.metric("Total applications", sum(counts.values()))
    for col, status in zip(st.columns(len(Status)), Status):
        col.metric(status.label, counts[status])

    st.subheader("Needs follow-up")
    today = date.today()
    due = repo.needs_follow_up(today=today)
    if not due:
        st.success("Nothing to follow up on today.")
        return

    st.dataframe(
        pd.DataFrame(
            {
                "Company": [a.company for a in due],
                "Role": [a.role for a in due],
                "Status": [a.status.label for a in due],
                "Follow-up": [a.follow_up_date for a in due],
                "Days overdue": [(today - a.follow_up_date).days for a in due],
            }
        ),
        hide_index=True,
        width="stretch",
        column_config={"Follow-up": st.column_config.DateColumn(format="YYYY-MM-DD")},
    )
