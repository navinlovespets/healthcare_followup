import pandas as pd
import streamlit as st

from dashboard import metrics
from dashboard.data_loader import load_base_data
from dashboard.filters import render_filters
from dashboard.page_common import render_dashboard_body, setup_page

setup_page("Doctor Wise — Creation Dashboard", "🩺")
st.caption("Follow-up creation performance by doctor, plus a clinic-wide total.")

df = load_base_data()
periods = metrics.build_periods(df)

filters = render_filters(df, exclude=("doctor",), key_prefix="doctor")

df_filtered = metrics.apply_global_filters(df, filters, exclude=("doctor",))

doctors = metrics.filter_options(df, "doctor")[1:]  # drop "All"
rows = [(doctor, df_filtered["vet_name"] == doctor) for doctor in doctors]
rows.append(("Total (all doctors)", pd.Series(True, index=df_filtered.index)))

render_dashboard_body(
    df_filtered,
    rows,
    periods,
    total_row_label="Total (all doctors)",
    group_label="Doctor",
    csv_prefix="doctor_wise",
)
