import streamlit as st

from dashboard import metrics
from dashboard.data_loader import load_base_data
from dashboard.ui import (
    ORG_KICKER,
    PRODUCT_NAME,
    divider,
    eyebrow,
    fmt_pct,
    inject_base_css,
    kpi_row,
    page_header,
)

st.set_page_config(page_title=PRODUCT_NAME, layout="wide")
inject_base_css()

page_header(
    ORG_KICKER,
    PRODUCT_NAME,
    "How reliably a completed appointment turns into a scheduled next step — "
    "tracked by episode type, clinic, and doctor, updated daily.",
)

df = load_base_data()
periods = metrics.build_periods(df)
snap = metrics.network_snapshot(df, periods)

_, fresh_col = st.columns([4, 1.3])
with fresh_col:
    if st.button("Refresh", icon=":material/refresh:", width="stretch"):
        load_base_data.clear()
        st.rerun()
    st.markdown(
        f'<div class="fp-freshness">Data as of {periods.max_date:%d %b %Y} '
        f"· refreshes on reopen after 30 min.</div>",
        unsafe_allow_html=True,
    )

st.write("")

delta = None
if snap["mtd_pct"] is not None and snap["lmtd_pct"] is not None:
    delta = f"{snap['mtd_pct'] - snap['lmtd_pct']:+.0f} pp vs last month"

kpi_row(
    [
        ("Completed cases · MTD", f"{int(snap['mtd_completed']):,}", None),
        ("Follow-ups created · MTD", f"{int(snap['mtd_followups']):,}", None),
        ("Network creation rate · MTD", fmt_pct(snap["mtd_pct"]), delta),
    ]
)

divider()
eyebrow("Explore")

cards = [
    (
        "pages/1_📋_Appointment_Type_Wise.py",
        "By episode type",
        "New Consultation, Vaccination and Follow Up, each split with and without an "
        "add-on service — plus Procedure and Diagnostic/Imaging visits.",
    ),
    (
        "pages/2_🏥_Clinic_Wise.py",
        "By clinic",
        "Every clinic side by side against a network-wide total, so a location's "
        "trend is easy to read in context.",
    ),
    (
        "pages/3_🩺_Doctor_Wise.py",
        "By doctor",
        "Individual doctor performance against a clinic-wide total, for coaching "
        "and performance conversations.",
    ),
]

cols = st.columns(3)
for col, (path, title, body) in zip(cols, cards):
    with col:
        with st.container(border=True):
            st.markdown('<div class="fp-card-marker"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fp-card-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fp-card-body">{body}</div>', unsafe_allow_html=True)
            st.page_link(path, label="Open dashboard →")

