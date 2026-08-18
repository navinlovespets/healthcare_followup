from datetime import date

import pandas as pd
import streamlit as st

from dashboard import metrics, metrics_show
from dashboard.data_loader import load_base_data
from dashboard.filters import render_show_filters
from dashboard.page_common_show import render_show_dashboard_body, setup_show_page

setup_show_page(
    "Show dashboard",
    "Clinic",
    "Of the follow-ups due at each clinic, how many actually showed up — "
    "against a network-wide total.",
)

df = load_base_data(date.today())
periods = metrics_show.build_show_periods(df)

filters, broad = render_show_filters(df, exclude=("clinic",), key_prefix="show_clinic")

df_filtered = metrics_show.apply_show_filters(df, filters, exclude=("clinic",))

clinics = metrics.filter_options(df, "clinic")[1:]  # drop "All"
rows = [(clinic, df_filtered["clinic"] == clinic) for clinic in clinics]
rows.append(("Total (all clinic)", pd.Series(True, index=df_filtered.index)))

render_show_dashboard_body(
    df_filtered,
    rows,
    periods,
    total_row_label="Total (all clinic)",
    group_label="Clinic",
    csv_prefix="show_clinic_wise",
    broad=broad,
)
