import streamlit as st

from extract import get_base_data
from transform import transform_data


@st.cache_data(ttl=1800, show_spinner="Pulling latest appointments from MySQL...")
def load_base_data():
    """
    Same extract -> transform pipeline that feeds BASE_DATA_ on Google Sheets,
    so every number in this app matches the sheet-based dashboards exactly.
    Cached for 30 minutes; use the sidebar "Refresh data" button to force a pull.
    """
    raw = get_base_data()
    return transform_data(raw)
