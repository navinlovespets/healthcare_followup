import streamlit as st

from dashboard import metrics_show as ms
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


def setup_show_page(kicker: str, title: str, subtitle: str):
    inject_base_css()
    page_header(kicker, title, subtitle)


def render_show_dashboard_body(
    df_filtered,
    rows: list[tuple[str, "object"]],
    periods,
    total_row_label: str,
    group_label: str,
    csv_prefix: str,
    broad: bool,
):
    completed = ms.build_show_table(rows, df_filtered, periods, "completed", broad)
    due = ms.build_show_table(rows, df_filtered, periods, "due", broad)
    shown = ms.build_show_table(rows, df_filtered, periods, "shown", broad)
    pct = ms.show_pct_table(due, shown)

    definition_label = "Broad (includes returned-in-window)" if broad else "Strict (exact due day only)"
    st.caption(
        f"{definition_label} · 4 trailing complete months, then last-month-to-date / "
        f"month-to-date (through {periods.max_date:%d %b %Y}), then a daily cut for the "
        f"current month — grouped by the follow-up's own due date, not the original visit date."
    )

    if total_row_label in due.index:
        mtd_due = due.loc[total_row_label, "MTD"]
        mtd_shown = shown.loc[total_row_label, "MTD"]
        mtd_pct = pct.loc[total_row_label, "MTD"]
        lmtd_pct = pct.loc[total_row_label, "LMTD"]
        delta = None
        if pct.loc[total_row_label, ["MTD", "LMTD"]].notna().all():
            delta = f"{mtd_pct - lmtd_pct:+.0f} pp vs last month"
        kpi_row(
            [
                ("Follow-ups due · MTD", f"{int(mtd_due):,}", None),
                ("Follow-ups shown · MTD", f"{int(mtd_shown):,}", None),
                ("Show rate · MTD", fmt_pct(mtd_pct), delta),
            ]
        )

    st.write("")
    tab_pct, tab_completed, tab_due, tab_shown, tab_trend = st.tabs(
        ["Show %", "Completed cases", "Due cases", "Shown cases", "Trend & comparison"]
    )

    with tab_pct:
        st.dataframe(style_pct_table(pct), width="stretch")
        st.download_button(
            "Download as CSV",
            pct.to_csv().encode("utf-8"),
            file_name=f"{csv_prefix}_show_pct.csv",
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

    with tab_due:
        st.dataframe(style_count_table(due), width="stretch")
        st.download_button(
            "Download as CSV",
            due.to_csv().encode("utf-8"),
            file_name=f"{csv_prefix}_due_cases.csv",
            key=f"{csv_prefix}_dl_due",
        )

    with tab_shown:
        st.dataframe(style_count_table(shown), width="stretch")
        st.download_button(
            "Download as CSV",
            shown.to_csv().encode("utf-8"),
            file_name=f"{csv_prefix}_shown_cases.csv",
            key=f"{csv_prefix}_dl_shown",
        )

    with tab_trend:
        daily_labels = [d.strftime("%d %b") for d in periods.daily]
        if total_row_label in pct.index:
            daily_series = pct.loc[total_row_label, daily_labels]
            st.plotly_chart(
                trend_line_chart(daily_series, f"Daily show rate — {total_row_label}"),
                width="stretch",
            )

        compare_rows = [r for r in pct.index if r != total_row_label]
        if compare_rows:
            top_n = None
            if len(compare_rows) > TOP_N_THRESHOLD:
                col_a, _ = st.columns([1, 3])
                top_n = col_a.selectbox(
                    "Show top",
                    [10, 15, 25, 50, "All"],
                    index=1,
                    key=f"{csv_prefix}_topn",
                )
                top_n = None if top_n == "All" else int(top_n)
            latest_mtd = pct.loc[compare_rows, "MTD"]
            st.plotly_chart(
                comparison_bar_chart(
                    latest_mtd, f"Month-to-date show rate by {group_label.lower()}", top_n=top_n
                ),
                width="stretch",
            )
