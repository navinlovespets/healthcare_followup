from datetime import date

import pandas as pd
import streamlit as st

from dashboard import metrics_show
from dashboard.data_loader import load_base_data
from dashboard.filters import render_show_filters
from dashboard.page_common_show import render_show_dashboard_body, setup_show_page

setup_show_page(
    "Show dashboard",
    "Follow-up Type",
    "Of the follow-ups due of each type, how many actually showed up — "
    "against a network-wide total. Follow-up type is the kind of appointment "
    "the follow-up itself is (Consult, Vaccination, Procedure, ...), not the "
    "original visit.",
)

df = load_base_data(date.today())
periods = metrics_show.build_show_periods(df)

# planned_followup_type was never offered as its own filter on this family's
# sheets, so nothing needs excluding here - unlike the other 3 pages.
filters, broad = render_show_filters(df, exclude=(), key_prefix="show_ftype")

df_filtered = metrics_show.apply_show_filters(df, filters, exclude=())

ftypes = metrics_show.followup_type_options(df)
rows = [(t, df_filtered["planned_followup_type"] == t) for t in ftypes]
rows.append(("Total (all followup type)", pd.Series(True, index=df_filtered.index)))

render_show_dashboard_body(
    df_filtered,
    rows,
    periods,
    total_row_label="Total (all followup type)",
    group_label="Follow-up Type",
    csv_prefix="show_followup_type_wise",
    broad=broad,
)
