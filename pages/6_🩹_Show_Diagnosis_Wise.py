from datetime import date

import pandas as pd
import streamlit as st

from dashboard import metrics, metrics_show
from dashboard.data_loader import load_base_data
from dashboard.filters import render_show_filters
from dashboard.page_common_show import render_show_dashboard_body, setup_show_page

setup_show_page(
    "Show % dashboard",
    "Diagnosis",
    "Of the follow-ups due for each diagnosis group, how many actually showed up — "
    "against a network-wide total.",
)

df = load_base_data(date.today())
periods = metrics_show.build_show_periods(df)

filters, broad = render_show_filters(df, exclude=("diagnosis_group",), key_prefix="show_diagnosis")

df_filtered = metrics_show.apply_show_filters(df, filters, exclude=("diagnosis_group",))

diagnoses = metrics.filter_options(df, "diagnosis_group")[1:]  # drop "All"
rows = [(d, df_filtered["mr_diagnosis_group"] == d) for d in diagnoses]
rows.append(("Total (all diagnosis)", pd.Series(True, index=df_filtered.index)))

render_show_dashboard_body(
    df_filtered,
    rows,
    periods,
    total_row_label="Total (all diagnosis)",
    group_label="Diagnosis",
    csv_prefix="show_diagnosis_wise",
    broad=broad,
)
