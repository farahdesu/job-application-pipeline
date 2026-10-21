"""Streamlit entry point: `streamlit run app.py`."""

import streamlit as st

from jobpipe.ui import add, applications, dashboard

st.set_page_config(page_title="Job Tracker", page_icon=":material/work:", layout="wide")

page = st.navigation(
    [
        st.Page(dashboard.render, title="Dashboard", icon=":material/dashboard:", url_path="dashboard", default=True),
        st.Page(applications.render, title="Applications", icon=":material/table_rows:", url_path="applications"),
        st.Page(add.render, title="Add application", icon=":material/add:", url_path="add"),
    ]
)
page.run()
