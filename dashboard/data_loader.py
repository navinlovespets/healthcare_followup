from datetime import date

import streamlit as st

from extract import get_base_data
from transform import transform_data


@st.cache_data(show_spinner="Pulling latest appointments from MySQL...")
def load_base_data(cache_date: date):
    """
    Same extract -> transform pipeline that feeds BASE_DATA_ on Google Sheets,
    so every number in this app matches the sheet-based dashboards exactly.

    The extract itself only ever covers through yesterday (see extract.py),
    so there's nothing to gain from refreshing within a day - cache_date is
    keyed to today's date, so this holds steady all day and only recomputes
    once the calendar date rolls over. The "Refresh now" button still forces
    an immediate pull regardless of date via load_base_data.clear().
    """
    raw = get_base_data()
    return transform_data(raw)
