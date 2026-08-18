from datetime import date

import streamlit as st

from dashboard import metrics
from dashboard.data_loader import load_base_data
from dashboard.filters import render_filters
from dashboard.page_common import render_dashboard_body, setup_page

setup_page(
    "Creation dashboard",
    "Appointment Type",
    "How often a completed visit turns into a scheduled follow-up, by episode type — "
    "New Consultation, Vaccination and Follow Up, each split with and without an add-on "
    "service, plus Procedure and Diagnostic/Imaging visits.",
)

df = load_base_data(date.today())
periods = metrics.build_periods(df)

filters = render_filters(df, exclude=(), key_prefix="apptype")

df_filtered = metrics.apply_global_filters(
    df, filters, exclude=("appointment_type",), include_vaccination_special=False
)

all_rows = metrics.episode_type_rows(df_filtered)

selected_type = filters.get("appointment_type", "All")
vacc_type = filters.get("vaccination_type", "All")
vacc_special = selected_type == "Vaccination" and vacc_type != "All"

rows = []
for label, mask, type_tag in all_rows:
    if type_tag is not None and selected_type != "All" and type_tag != selected_type:
        continue  # hidden: matches the sheet's zero-out rule for a mismatched Appointment Type filter
    if vacc_special and type_tag == "Vaccination":
        mask = mask & (df_filtered[metrics.VACCINATION_TYPE_COLUMN] == vacc_type)
    rows.append((label, mask))

if not rows:
    st.warning("No episode types match the current Appointment Type filter.")
else:
    render_dashboard_body(
        df_filtered,
        rows,
        periods,
        total_row_label="Total (all episode types)",
        group_label="Episode Type",
        csv_prefix="appt_type_wise",
    )
