import streamlit as st

from dashboard.metrics import FILTER_LABELS, filter_options

FILTER_ORDER = [
    "clinic",
    "doctor",
    "appointment_type",
    "customer_type",
    "species",
    "age_bucket",
    "vaccination_type",
    "diagnosis_group",
]


def render_filters(df, exclude: tuple = (), key_prefix: str = "") -> dict:
    st.sidebar.subheader("Filters")
    selections = {}
    for key in FILTER_ORDER:
        if key in exclude:
            continue
        options = filter_options(df, key)
        selections[key] = st.sidebar.selectbox(
            FILTER_LABELS[key], options, index=0, key=f"{key_prefix}_{key}"
        )

    if "vaccination_type" in selections and selections.get("appointment_type") != "Vaccination":
        st.sidebar.caption(
            "Vaccination Type only applies once Appointment Type is set to \"Vaccination\"."
        )

    if st.sidebar.button("Reset filters", key=f"{key_prefix}_reset"):
        for key in FILTER_ORDER:
            state_key = f"{key_prefix}_{key}"
            if state_key in st.session_state:
                del st.session_state[state_key]
        st.rerun()

    return selections
