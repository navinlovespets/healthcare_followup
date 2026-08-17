"""Shared look-and-feel: palette, KPI tiles, styled tables, charts."""

import matplotlib.colors as mcolors
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Validated palette (see dataviz skill references/palette.md)
SEQUENTIAL_BLUE_STEPS = [
    "#f7fafd", "#cde2fb", "#9ec5f4", "#6da7ec",
    "#3987e5", "#256abf", "#184f95", "#0d366b",
]
SERIES_BLUE = "#2a78d6"
SERIES_BLUE_DARK = "#3987e5"
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"
TEXT_MUTED = "#8a897f"

_PCT_CMAP = mcolors.LinearSegmentedColormap.from_list("creation_pct", SEQUENTIAL_BLUE_STEPS)


def inject_base_css():
    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            background: color-mix(in srgb, currentColor 4%, transparent);
            border: 1px solid color-mix(in srgb, currentColor 12%, transparent);
            border-radius: 10px;
            padding: 14px 16px 10px 16px;
        }
        .dash-caption {
            color: #8a897f;
            font-size: 0.85rem;
            margin-top: -8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list[tuple[str, str, str | None]]):
    """items: list of (label, value, delta) — delta may be None."""
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        col.metric(label, value, delta)


def fmt_count(n) -> str:
    if n is None or pd.isna(n):
        return "—"
    return f"{int(n):,}"


def fmt_pct(p) -> str:
    if p is None or pd.isna(p):
        return "—"
    return f"{p:.0f}%"


def style_count_table(df: pd.DataFrame):
    return df.style.format(fmt_count).set_properties(**{"text-align": "right"})


def style_pct_table(df: pd.DataFrame):
    return (
        df.style.format(fmt_pct)
        .background_gradient(cmap=_PCT_CMAP, vmin=0, vmax=100, axis=None)
        .set_properties(**{"text-align": "right"})
    )


def trend_line_chart(series: pd.Series, title: str, y_suffix: str = "%"):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=list(series.index),
            y=series.values,
            mode="lines+markers",
            line=dict(color=SERIES_BLUE, width=2),
            marker=dict(size=6),
            hovertemplate="%{x}: %{y:.0f}" + y_suffix + "<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(ticksuffix=y_suffix, gridcolor="rgba(128,128,128,0.15)", zeroline=False),
        xaxis=dict(gridcolor="rgba(128,128,128,0.05)"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def comparison_bar_chart(series: pd.Series, title: str, y_suffix: str = "%"):
    ordered = series.dropna().sort_values(ascending=True)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=ordered.values,
            y=list(ordered.index),
            orientation="h",
            marker=dict(color=SERIES_BLUE),
            hovertemplate="%{y}: %{x:.0f}" + y_suffix + "<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=max(280, 28 * len(ordered)),
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(ticksuffix=y_suffix, gridcolor="rgba(128,128,128,0.15)", zeroline=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
