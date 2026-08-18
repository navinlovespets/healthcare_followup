"""Shared look-and-feel: brand system, headers, KPI tiles, styled tables, charts."""

import matplotlib.colors as mcolors
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Brand
# ---------------------------------------------------------------------------
PRODUCT_NAME = "Follow-up Performance"
ORG_KICKER = "Supertails · Clinic Analytics"

# Validated palette (see dataviz skill references/palette.md)
SEQUENTIAL_BLUE_STEPS = [
    "#f7fafd", "#cde2fb", "#9ec5f4", "#6da7ec",
    "#3987e5", "#256abf", "#184f95", "#0d366b",
]
SERIES_BLUE = "#2a78d6"
SERIES_BLUE_SOFT = "rgba(42, 120, 214, 0.12)"
STATUS_GOOD = "#0ca30c"
STATUS_CRITICAL = "#d03b3b"
TEXT_MUTED = "#7c7b73"

_PCT_CMAP = mcolors.LinearSegmentedColormap.from_list("creation_pct", SEQUENTIAL_BLUE_STEPS)
_PCT_CMAP.set_bad(color="#eceae4")  # matplotlib defaults NaN to black otherwise


def inject_base_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class^="st-"], [class*=" st-"], [data-testid="stAppViewContainer"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        footer { visibility: hidden; }
        header[data-testid="stHeader"] { background: transparent; }

        .block-container { padding-top: 2.2rem; max-width: 1200px; }

        /* ---- Page header ------------------------------------------------ */
        .fp-kicker {
            text-transform: uppercase;
            letter-spacing: .14em;
            font-size: .72rem;
            font-weight: 700;
            color: #2a78d6;
            margin: 0 0 6px 0;
        }
        .fp-title {
            font-size: 2.05rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0 0 6px 0;
            line-height: 1.15;
        }
        .fp-subtitle {
            color: #7c7b73;
            font-size: 1rem;
            max-width: 780px;
            line-height: 1.5;
            margin: 0;
        }
        .fp-divider {
            height: 1px;
            background: linear-gradient(90deg, rgba(42,120,214,.35), rgba(128,128,128,.08));
            border: none;
            margin: 22px 0 28px 0;
        }
        .fp-eyebrow {
            text-transform: uppercase;
            letter-spacing: .1em;
            font-size: .7rem;
            font-weight: 700;
            color: #a8a79c;
            margin: 30px 0 2px 0;
        }

        /* ---- KPI tiles ---------------------------------------------------*/
        div[data-testid="stMetric"] {
            background: color-mix(in srgb, currentColor 3%, transparent);
            border: 1px solid color-mix(in srgb, currentColor 10%, transparent);
            border-top: 3px solid #2a78d6;
            border-radius: 8px;
            padding: 14px 18px 12px 18px;
        }
        div[data-testid="stMetricLabel"] {
            font-size: .78rem;
            text-transform: uppercase;
            letter-spacing: .06em;
            font-weight: 600;
            opacity: .65;
        }
        div[data-testid="stMetricValue"] { font-weight: 800; }

        /* ---- Nav / info cards --------------------------------------------*/
        div[data-testid="stVerticalBlockBorderWrapper"]:has(div.fp-card-marker) {
            border-radius: 10px;
            transition: border-color .15s ease;
        }
        .fp-card-eyebrow {
            font-size: .72rem;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
            color: #2a78d6;
            margin-bottom: 2px;
        }
        .fp-card-title { font-size: 1.15rem; font-weight: 700; margin: 0 0 6px 0; }
        .fp-card-body { color: #7c7b73; font-size: .9rem; line-height: 1.5; min-height: 44px; }

        .fp-footnote { color: #a8a79c; font-size: .8rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(kicker: str, title: str, subtitle: str = ""):
    subtitle_html = f'<p class="fp-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="fp-kicker">{kicker}</div>
        <div class="fp-title">{title}</div>
        {subtitle_html}
        """,
        unsafe_allow_html=True,
    )


def eyebrow(text: str):
    st.markdown(f'<div class="fp-eyebrow">{text}</div>', unsafe_allow_html=True)


def divider():
    st.markdown('<hr class="fp-divider" />', unsafe_allow_html=True)


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
    # Streamlit's dataframe renderer reads a Styler's raw cell values for null
    # detection and prints a literal "None" for NaN, ignoring .format()/na_rep
    # entirely - so the table handed to it must already be display-ready
    # strings, never real NaN.
    return df.map(fmt_count).style.set_properties(**{"text-align": "right"})


def style_pct_table(df: pd.DataFrame):
    display_df = df.map(fmt_pct)
    return (
        display_df.style
        .background_gradient(cmap=_PCT_CMAP, gmap=df, vmin=0, vmax=100, axis=None)
        .set_properties(**{"text-align": "right"})
    )


_CHART_LAYOUT = dict(
    font=dict(family="Inter, -apple-system, Segoe UI, sans-serif", size=13),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=30, t=44, b=10),
)


def trend_line_chart(series: pd.Series, title: str, y_suffix: str = "%"):
    x = list(series.index)
    y = series.values

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            line=dict(color=SERIES_BLUE, width=2.5, shape="spline", smoothing=0.3),
            marker=dict(size=5, color=SERIES_BLUE),
            fill="tozeroy",
            fillcolor=SERIES_BLUE_SOFT,
            hovertemplate="%{x}: %{y:.0f}" + y_suffix + "<extra></extra>",
        )
    )

    # Direct-label only the latest point, not every marker.
    valid = series.dropna()
    if len(valid):
        last_x, last_y = valid.index[-1], valid.iloc[-1]
        fig.add_annotation(
            x=last_x,
            y=last_y,
            text=f"<b>{last_y:.0f}{y_suffix}</b>",
            showarrow=False,
            yshift=16,
            font=dict(size=12, color=SERIES_BLUE),
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, weight=600)),
        height=320,
        showlegend=False,
        yaxis=dict(
            ticksuffix=y_suffix,
            gridcolor="rgba(128,128,128,0.12)",
            zeroline=False,
            rangemode="tozero",
        ),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
        **_CHART_LAYOUT,
    )
    return fig


def comparison_bar_chart(series: pd.Series, title: str, y_suffix: str = "%", top_n: int | None = None):
    clean = series.dropna()
    if top_n is not None and len(clean) > top_n:
        clean = clean.nlargest(top_n)
    ordered = clean.sort_values(ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=ordered.values,
            y=list(ordered.index),
            orientation="h",
            marker=dict(color=SERIES_BLUE),
            text=[f"{v:.0f}{y_suffix}" for v in ordered.values],
            textposition="outside",
            textfont=dict(size=12, color=TEXT_MUTED),
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.0f}" + y_suffix + "<extra></extra>",
        )
    )
    max_val = float(ordered.max()) if len(ordered) else 0
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, weight=600)),
        height=max(260, 30 * len(ordered) + 60),
        xaxis=dict(
            ticksuffix=y_suffix,
            gridcolor="rgba(128,128,128,0.12)",
            zeroline=False,
            range=[0, max_val * 1.22 if max_val else 1],
        ),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        **_CHART_LAYOUT,
    )
    return fig
