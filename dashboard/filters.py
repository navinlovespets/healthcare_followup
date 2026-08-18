import streamlit as st

from dashboard.metrics import FILTER_LABELS, filter_options
from dashboard.metrics_show import SHOW_DEFINITION_OPTIONS

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

SHOW_FILTER_ORDER = [
    "clinic",
    "doctor",
    "species",
    "age_bucket",
    "appointment_type",
    "customer_type",
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


def render_show_filters(df, exclude: tuple = (), key_prefix: str = "") -> tuple[dict, bool]:
    """Same idea as render_filters, but for the Show% family: no Vaccination
    Type (never used there), plus the Strict/Broad show-definition toggle.
    Returns (filter_selections, broad: bool).
    """
    st.sidebar.subheader("Show % definition")
    definition = st.sidebar.selectbox(
        "Select Show % Definition",
        SHOW_DEFINITION_OPTIONS,
        index=0,
        key=f"{key_prefix}_definition",
        help="Strict = attended on the exact due day. Broad = also counts a "
        "later qualifying return within the window as success.",
    )
    broad = definition == SHOW_DEFINITION_OPTIONS[0]

    st.sidebar.subheader("Filters")
    selections = {}
    for key in SHOW_FILTER_ORDER:
        if key in exclude:
            continue
        options = filter_options(df, key)
        selections[key] = st.sidebar.selectbox(
            FILTER_LABELS[key], options, index=0, key=f"{key_prefix}_{key}"
        )

    if st.sidebar.button("Reset filters", key=f"{key_prefix}_reset"):
        for key in SHOW_FILTER_ORDER:
            state_key = f"{key_prefix}_{key}"
            if state_key in st.session_state:
                del st.session_state[state_key]
        state_key = f"{key_prefix}_definition"
        if state_key in st.session_state:
            del st.session_state[state_key]
        st.rerun()

    return selections, broad
