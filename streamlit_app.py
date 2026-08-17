import streamlit as st

from dashboard.data_loader import load_base_data
from dashboard.ui import inject_base_css

st.set_page_config(
    page_title="Healthcare Follow-up Dashboards",
    page_icon="🏥",
    layout="wide",
)
inject_base_css()

st.title("🏥 Healthcare Follow-up Dashboards")
st.caption("Migrated from Google Sheets — same data, filters and numbers, now interactive.")

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh data", width="stretch"):
        load_base_data.clear()
        st.rerun()

with st.spinner("Loading appointment data..."):
    df = load_base_data()

as_of = df["appointment_date"].max()
st.success(
    f"Loaded **{len(df):,}** completed & no-show appointment records "
    f"— data through **{as_of:%d %b %Y}**."
)

st.markdown("### Creation Dashboard")
st.markdown(
    """
This first migration covers the three **Follow-up Creation %** dashboards — how
often a follow-up gets *created* for a completed appointment, sliced three ways.
Every page carries the same 7 shared filters (Clinic, Doctor, Appointment Type,
Customer Type, Species, Age Bucket, Vaccination Type, Diagnosis Group) as the
Sheets version, plus the same time cuts: 4 trailing complete months, LMTD, MTD
and a daily trend for the current month.

Use the sidebar to open a dashboard:

- **📋 Appointment Type Wise** — New Consultation / Vaccination / Follow Up
  (with an "without add-on service" cut), Procedure, Diagnostic/Imaging, and a
  grand total.
- **🏥 Clinic Wise** — every clinic, plus a network-wide total.
- **🩺 Doctor Wise** — every doctor on staff, plus a total.

Each page shows **Total Completed Cases**, **Total Follow-ups Created**, and the
resulting **Creation %**, as KPI tiles, a heatmapped table, and trend/comparison
charts.
"""
)

st.markdown("### Data pipeline")
st.markdown(
    """
Numbers here come straight from the same MySQL extract + transform pipeline
(`extract.py` → `transform.py`) that feeds the `BASE_DATA_` tab powering the
Sheets dashboards — so this app and the Sheets stay in lockstep. Cached for 30
minutes; hit **Refresh data** above to force a re-pull.
"""
)
