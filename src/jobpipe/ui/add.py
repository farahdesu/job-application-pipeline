import streamlit as st

from jobpipe.ui.components import application_form, flash, get_repo, show_flash

# Bumped after each save so the form remounts empty.
_FORM_VERSION_KEY = "add_form_version"


def render() -> None:
    show_flash()
    st.title("Add application")

    version = st.session_state.setdefault(_FORM_VERSION_KEY, 0)
    data = application_form(key=f"add-form-{version}")
    if data is not None:
        created = get_repo().create(data)
        flash(f"Added {created.role} at {created.company}")
        st.session_state[_FORM_VERSION_KEY] = version + 1
        st.rerun()
