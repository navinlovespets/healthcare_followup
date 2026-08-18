from datetime import date

import pandas as pd
import streamlit as st

from dashboard import metrics
from dashboard.data_loader import load_base_data
from dashboard.filters import render_filters
from dashboard.page_common import render_dashboard_body, setup_page

setup_page(
    "Creation dashboard",
    "Clinic",
    "How reliably each clinic turns a completed visit into a scheduled follow-up, "
    "with a network-wide total for context.",
)

df = load_base_data(date.today())
periods = metrics.build_periods(df)

filters = render_filters(df, exclude=("clinic",), key_prefix="clinic")

df_filtered = metrics.apply_global_filters(df, filters, exclude=("clinic",))

clinics = metrics.filter_options(df, "clinic")[1:]  # drop "All"
rows = [(clinic, df_filtered["clinic"] == clinic) for clinic in clinics]
rows.append(("Total (all clinics)", pd.Series(True, index=df_filtered.index)))

render_dashboard_body(
    df_filtered,
    rows,
    periods,
    total_row_label="Total (all clinics)",
    group_label="Clinic",
    csv_prefix="clinic_wise",
)
