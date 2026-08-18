import streamlit as st

from dashboard import metrics
from dashboard.ui import (
    comparison_bar_chart,
    fmt_pct,
    inject_base_css,
    kpi_row,
    page_header,
    style_count_table,
    style_pct_table,
    trend_line_chart,
)

TOP_N_THRESHOLD = 18
TOP_N_DEFAULT = 12


def setup_page(page_title: str, kicker: str, title: str, subtitle: str):
    st.set_page_config(page_title=f"{page_title} — Follow-up Performance", layout="wide")
    inject_base_css()
    page_header(kicker, title, subtitle)


def render_dashboard_body(
    df_filtered,
    rows: list[tuple[str, "object"]],
    periods: metrics.Periods,
    total_row_label: str,
    group_label: str,
    csv_prefix: str,
):
    completed = metrics.build_table(rows, df_filtered, periods, followup_only=False)
    followups = metrics.build_table(rows, df_filtered, periods, followup_only=True)
    pct = metrics.creation_pct_table(completed, followups)

    st.caption(
        f"4 trailing complete months, then last-month-to-date / month-to-date "
        f"(through {periods.max_date:%d %b %Y}), then a daily cut for the current month."
    )

    if total_row_label in completed.index:
        mtd_completed = completed.loc[total_row_label, "MTD"]
        mtd_followups = followups.loc[total_row_label, "MTD"]
        mtd_pct = pct.loc[total_row_label, "MTD"]
        lmtd_pct = pct.loc[total_row_label, "LMTD"]
        delta = None
        if pct.loc[total_row_label, ["MTD", "LMTD"]].notna().all():
            delta = f"{mtd_pct - lmtd_pct:+.0f} pp vs last month"
        kpi_row(
            [
                ("Completed cases · MTD", f"{int(mtd_completed):,}", None),
                ("Follow-ups created · MTD", f"{int(mtd_followups):,}", None),
                ("Creation rate · MTD", fmt_pct(mtd_pct), delta),
            ]
        )

    st.write("")
    tab_pct, tab_completed, tab_followups, tab_trend = st.tabs(
        ["Creation rate", "Completed cases", "Follow-ups created", "Trend & comparison"]
    )

    with tab_pct:
        st.dataframe(style_pct_table(pct), width="stretch")
        st.download_button(
            "Download as CSV",
            pct.to_csv().encode("utf-8"),
            file_name=f"{csv_prefix}_creation_pct.csv",
            key=f"{csv_prefix}_dl_pct",
        )

    with tab_completed:
        st.dataframe(style_count_table(completed), width="stretch")
        st.download_button(
            "Download as CSV",
            completed.to_csv().encode("utf-8"),
            file_name=f"{csv_prefix}_completed_cases.csv",
            key=f"{csv_prefix}_dl_completed",
        )

    with tab_followups:
        st.dataframe(style_count_table(followups), width="stretch")
        st.download_button(
            "Download as CSV",
            followups.to_csv().encode("utf-8"),
            file_name=f"{csv_prefix}_followups_created.csv",
            key=f"{csv_prefix}_dl_followups",
        )

    with tab_trend:
        daily_labels = [d.strftime("%d %b") for d in periods.daily]
        if total_row_label in pct.index:
            daily_series = pct.loc[total_row_label, daily_labels]
            st.plotly_chart(
                trend_line_chart(daily_series, f"Daily creation rate — {total_row_label}"),
                width="stretch",
            )

        compare_rows = [r for r in pct.index if r != total_row_label and "↳" not in r]
        if compare_rows:
            top_n = None
            if len(compare_rows) > TOP_N_THRESHOLD:
                col_a, _ = st.columns([1, 3])
                top_n = col_a.selectbox(
                    f"Show top",
                    [10, 15, 25, 50, "All"],
                    index=1,
                    key=f"{csv_prefix}_topn",
                )
                top_n = None if top_n == "All" else int(top_n)
            latest_mtd = pct.loc[compare_rows, "MTD"]
            st.plotly_chart(
                comparison_bar_chart(
                    latest_mtd, f"Month-to-date creation rate by {group_label.lower()}", top_n=top_n
                ),
                width="stretch",
            )
