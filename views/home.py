from datetime import date

import streamlit as st

from dashboard import metrics, metrics_show
from dashboard.data_loader import load_base_data
from dashboard.ui import (
    ORG_KICKER,
    PRODUCT_NAME,
    divider,
    eyebrow,
    fmt_pct,
    kpi_row,
    page_header,
)

df = load_base_data(date.today())
periods = metrics.build_periods(df)
snap = metrics.network_snapshot(df, periods)
show_periods = metrics_show.build_show_periods(df)
show_snap = metrics_show.network_show_snapshot(df, show_periods, broad=True)

header_col, fresh_col = st.columns([2.6, 1.4], gap="large")
with header_col:
    page_header(
        ORG_KICKER,
        PRODUCT_NAME,
        "How reliably a completed appointment turns into a scheduled next step, "
        "and how often a due follow-up actually shows — tracked by episode type, "
        "clinic, doctor, customer type, diagnosis, and follow-up type.",
    )
with fresh_col:
    if st.button(
        f"Data as of {periods.max_date:%d %b %Y} · Refresh",
        icon=":material/refresh:",
        width="stretch",
    ):
        load_base_data.clear()
        st.rerun()
    st.markdown(
        '<div class="fp-freshness">Refreshes automatically once a day.</div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Creation - network snapshot
# ---------------------------------------------------------------------------
st.write("")
eyebrow("Creation — network snapshot")

creation_delta = None
if snap["mtd_pct"] is not None and snap["lmtd_pct"] is not None:
    creation_delta = f"{snap['mtd_pct'] - snap['lmtd_pct']:+.0f} pp vs last month"

kpi_row(
    [
        ("Completed cases · MTD", f"{int(snap['mtd_completed']):,}", None),
        ("Follow-ups created · MTD", f"{int(snap['mtd_followups']):,}", None),
        ("Creation rate · MTD", fmt_pct(snap["mtd_pct"]), creation_delta),
    ]
)
st.write("")
kpi_row(
    [
        ("Completed cases · LMTD", f"{int(snap['lmtd_completed']):,}", None),
        ("Follow-ups created · LMTD", f"{int(snap['lmtd_followups']):,}", None),
        ("Creation rate · LMTD", fmt_pct(snap["lmtd_pct"]), None),
    ]
)
st.write("")
kpi_row(
    [
        (f"{label} creation rate", fmt_pct(pct), None)
        for label, pct in snap["monthly_pct"].items()
    ]
)

# ---------------------------------------------------------------------------
# Show % - network snapshot
# ---------------------------------------------------------------------------
st.write("")
eyebrow("Show — network snapshot")
st.caption("Broad definition (includes a qualifying return within the window).")

show_delta = None
if show_snap["mtd_pct"] is not None and show_snap["lmtd_pct"] is not None:
    show_delta = f"{show_snap['mtd_pct'] - show_snap['lmtd_pct']:+.0f} pp vs last month"

kpi_row(
    [
        ("Follow-ups due · MTD", f"{int(show_snap['mtd_due']):,}", None),
        ("Follow-ups shown · MTD", f"{int(show_snap['mtd_shown']):,}", None),
        ("Show rate · MTD", fmt_pct(show_snap["mtd_pct"]), show_delta),
    ]
)
st.write("")
kpi_row(
    [
        ("Follow-ups due · LMTD", f"{int(show_snap['lmtd_due']):,}", None),
        ("Follow-ups shown · LMTD", f"{int(show_snap['lmtd_shown']):,}", None),
        ("Show rate · LMTD", fmt_pct(show_snap["lmtd_pct"]), None),
    ]
)
st.write("")
kpi_row(
    [
        (f"{label} show rate", fmt_pct(pct), None)
        for label, pct in show_snap["monthly_pct"].items()
    ]
)

# ---------------------------------------------------------------------------
# Navigation cards
# ---------------------------------------------------------------------------
divider()
eyebrow("Creation dashboard")
st.caption("Did a completed visit get a follow-up scheduled at all?")

creation_cards = [
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
for col, (path, title, body) in zip(cols, creation_cards):
    with col:
        with st.container(border=True):
            st.markdown('<div class="fp-card-marker"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fp-card-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fp-card-body">{body}</div>', unsafe_allow_html=True)
            st.page_link(path, label="Open dashboard →")

st.write("")
eyebrow("Show dashboard")
st.caption("Of the follow-ups that were due, how many actually showed up?")

show_cards = [
    (
        "pages/4_🏥_Show_Clinic_Wise.py",
        "By clinic",
        "Due vs. shown for every clinic, against a network-wide total.",
    ),
    (
        "pages/5_🧑_Show_Customer_Type_Wise.py",
        "By customer type",
        "New-to-brand, new-to-platform, and repeat customers, compared side by side.",
    ),
    (
        "pages/6_🩹_Show_Diagnosis_Wise.py",
        "By diagnosis",
        "Which diagnosis groups reliably bring customers back for their follow-up.",
    ),
    (
        "pages/7_🔁_Show_Followup_Type_Wise.py",
        "By follow-up type",
        "Whether the follow-up itself was a consult, vaccination, procedure, or other visit type.",
    ),
]

cols2 = st.columns(4)
for col, (path, title, body) in zip(cols2, show_cards):
    with col:
        with st.container(border=True):
            st.markdown('<div class="fp-card-marker"></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fp-card-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="fp-card-body">{body}</div>', unsafe_allow_html=True)
            st.page_link(path, label="Open dashboard →")
