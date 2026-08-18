from datetime import date

import pandas as pd
import streamlit as st

from dashboard import metrics, metrics_show
from dashboard.data_loader import load_base_data
from dashboard.filters import render_show_filters
from dashboard.page_common_show import render_show_dashboard_body, setup_show_page

setup_show_page(
    "Show % dashboard",
    "Customer Type",
    "Of the follow-ups due for each customer type, how many actually showed up — "
    "against a network-wide total.",
)

df = load_base_data(date.today())
periods = metrics_show.build_show_periods(df)

filters, broad = render_show_filters(df, exclude=("customer_type",), key_prefix="show_custtype")

df_filtered = metrics_show.apply_show_filters(df, filters, exclude=("customer_type",))

cust_types = metrics.filter_options(df, "customer_type")[1:]  # drop "All"
rows = [(ct, df_filtered["customer_segment"] == ct) for ct in cust_types]
rows.append(("Total (all customer type)", pd.Series(True, index=df_filtered.index)))

render_show_dashboard_body(
    df_filtered,
    rows,
    periods,
    total_row_label="Total (all customer type)",
    group_label="Customer Type",
    csv_prefix="show_customer_type_wise",
    broad=broad,
)
