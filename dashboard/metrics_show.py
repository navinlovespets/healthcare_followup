"""
Follow-up Show % engine - "Due vs Shown" family.

Reproduces, in pandas, the exact COUNTIFS logic used on the "Followup Show% -
Due vs Shown - Clinic / Customer Type / Diagnosis / Followup Type" sheets.

Unlike the Creation % family (metrics.py), which is anchored on TODAY() /
MAX(appointment_date), this family is anchored on
MAX(planned_followup_actual_date) - the follow-up's own due date - per the
sheet's "Data Anchor (last date in source)" cell (=MAX(BASE_DATA_!$AE:$AE)).
Every period (trailing 4 months, LMTD, MTD, daily) is computed off that
anchor's month, not off the calendar today().

Three blocks per row:
  Total Completed Cases = count(no_show=0, appointment_date in period, <row>, <filters>)
  Total Follow-up Cases (Due) = count(return_reason not in DUE_EXCLUDED,
                                       planned_followup_actual_date in period, <row>, <filters>)
  Total Show Cases (Shown) = count(return_reason == "Planned follow-up attended", same period/row/filters)
                              + (if Broad) count(return_reason == "Returned in follow-up window", same)
  Show % = Shown / Due

Column letters from the sheet map to BASE_DATA_ columns as:
  AE=planned_followup_actual_date  AF=planned_followup_type  AL=return_reason
  (all other filter/date columns match metrics.py's mapping)
"""

from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta

from dashboard.metrics import FILTER_TO_COLUMN, Periods, _bucket_counts, _daily_counts

SHOW_FILTER_TO_COLUMN = {k: v for k, v in FILTER_TO_COLUMN.items()}  # no vaccination_type in this family

DUE_EXCLUDED_REASONS = {
    "Follow-up not created",
    "Initial appointment no-show",
    "Follow-up appointment not found",
}
SHOW_STRICT_REASONS = {"Planned follow-up attended"}
SHOW_BROAD_EXTRA_REASON = "Returned in follow-up window"

SHOW_DEFINITION_OPTIONS = [
    "Broad - Includes Returned-in-Window",
    "Strict - Exact Due Day Only",
]


def followup_type_options(df: pd.DataFrame) -> list:
    """planned_followup_type isn't a filter (it's only ever a row dimension,
    on the Followup Type sheet), so it isn't in FILTER_TO_COLUMN."""
    return sorted(
        v
        for v in df["planned_followup_type"].dropna().unique()
        if str(v).strip() not in ("", "NA")
    )


def apply_show_filters(df: pd.DataFrame, filters: dict, exclude: tuple = ()) -> pd.DataFrame:
    """Same 7-filter set as Creation, minus Vaccination Type - this family never uses it."""
    mask = pd.Series(True, index=df.index)
    for key, col in SHOW_FILTER_TO_COLUMN.items():
        if key in exclude:
            continue
        val = filters.get(key, "All")
        if val and val != "All":
            mask &= df[col] == val
    return df[mask]


def build_show_periods(df: pd.DataFrame) -> Periods:
    """
    Anchored on MAX(planned_followup_actual_date), matching the sheet's
    Data Anchor cell - not on today() or on the appointment_date anchor used
    for Creation dashboards.
    """
    anchor = df["planned_followup_actual_date"].max()
    if pd.isna(anchor):
        anchor = pd.Timestamp(date.today())
    anchor = pd.Timestamp(anchor).normalize()

    mtd_start = anchor.replace(day=1)
    mtd_end = anchor

    lmtd_start = mtd_start - relativedelta(months=1)
    lmtd_end = anchor - relativedelta(months=1)

    months = []
    for i in range(4, 0, -1):
        m_start = mtd_start - relativedelta(months=i)
        m_end = m_start + relativedelta(months=1) - pd.Timedelta(days=1)
        months.append((m_start.strftime("%b '%y"), m_start, m_end))

    daily = pd.date_range(mtd_start, mtd_end, freq="D")

    return Periods(
        months=months,
        lmtd=("LMTD", lmtd_start, lmtd_end),
        mtd=("MTD", mtd_start, mtd_end),
        daily=daily,
        max_date=anchor,
    )


def _block_population(subset: pd.DataFrame, block: str, broad: bool) -> tuple[pd.DataFrame, str]:
    if block == "completed":
        return subset[subset["no_show"] == 0], "appointment_date"
    if block == "due":
        return subset[~subset["return_reason"].isin(DUE_EXCLUDED_REASONS)], "planned_followup_actual_date"
    if block == "shown":
        reasons = set(SHOW_STRICT_REASONS)
        if broad:
            reasons.add(SHOW_BROAD_EXTRA_REASON)
        return subset[subset["return_reason"].isin(reasons)], "planned_followup_actual_date"
    raise ValueError(f"Unknown block: {block}")


def show_row_counts(subset: pd.DataFrame, periods: Periods, block: str, broad: bool) -> dict:
    pop, date_col = _block_population(subset, block, broad)
    row = _bucket_counts(pop[date_col], periods.monthly_buckets)
    row.update(_daily_counts(pop[date_col], periods.daily))
    return row


def build_show_table(rows: list, df: pd.DataFrame, periods: Periods, block: str, broad: bool) -> pd.DataFrame:
    labels = [label for label, _ in rows]
    records = [show_row_counts(df[mask], periods, block, broad) for _, mask in rows]
    return pd.DataFrame(records, index=labels)


def show_pct_table(due: pd.DataFrame, shown: pd.DataFrame) -> pd.DataFrame:
    denom = due.mask(due == 0)
    return (shown / denom) * 100


def network_show_snapshot(df: pd.DataFrame, periods: Periods, broad: bool) -> dict:
    """
    Unfiltered, whole-network MTD / LMTD / trailing-month show rate - used for
    the home page. Mirrors metrics.network_snapshot's shape.
    """
    due = show_row_counts(df, periods, "due", broad)
    shown = show_row_counts(df, periods, "shown", broad)
    mtd_due, lmtd_due = due["MTD"], due["LMTD"]
    mtd_shown, lmtd_shown = shown["MTD"], shown["LMTD"]

    monthly_pct = {}
    for label, _, _ in periods.months:
        d, s = due[label], shown[label]
        monthly_pct[label] = (s / d * 100) if d else None

    return {
        "mtd_due": mtd_due,
        "mtd_shown": mtd_shown,
        "mtd_pct": (mtd_shown / mtd_due * 100) if mtd_due else None,
        "lmtd_due": lmtd_due,
        "lmtd_shown": lmtd_shown,
        "lmtd_pct": (lmtd_shown / lmtd_due * 100) if lmtd_due else None,
        "monthly_pct": monthly_pct,
    }
