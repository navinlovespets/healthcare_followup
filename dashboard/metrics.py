"""
Creation % engine.

Reproduces, in pandas, the exact COUNTIFS logic used on the "Creation% - Appt
Type Wise", "Creation% - Clinic Wise" and "Creation% - Doctor Wise" sheets:

  Total Completed Cases  = count(no_show = 0, <row condition>, <filters>, <period>)
  Total Followup Cases   = count(no_show = 0, followup_app_id not null, <row condition>, <filters>, <period>)
  Followup / Creation %  = Followup Cases / Completed Cases

Column letters from the sheet map to BASE_DATA_ columns as:
  X=no_show  Z=followup_app_id  D=appointment_type  F=clinic  N=vet_name
  M=customer_segment  T=species  AO=age_group  AP=Combined (vaccination_category|age_group)
  AB=mr_diagnosis_group  AT=lab_imaging_flag  AU=procedure_flag  C=appointment_date
"""

from dataclasses import dataclass, field
from datetime import date

import pandas as pd
from dateutil.relativedelta import relativedelta

FILTER_TO_COLUMN = {
    "clinic": "clinic",
    "doctor": "vet_name",
    "appointment_type": "appointment_type",
    "customer_type": "customer_segment",
    "species": "species",
    "age_bucket": "age_group",
    "diagnosis_group": "mr_diagnosis_group",
}

VACCINATION_TYPE_COLUMN = "Combined"

FILTER_LABELS = {
    "clinic": "Clinic",
    "doctor": "Doctor",
    "appointment_type": "Appointment Type",
    "customer_type": "Customer Type",
    "species": "Species",
    "age_bucket": "Age Bucket",
    "vaccination_type": "Vaccination Type",
    "diagnosis_group": "Diagnosis Group",
}

ALL_FILTER_KEYS = list(FILTER_TO_COLUMN.keys()) + ["vaccination_type"]


def filter_options(df: pd.DataFrame, key: str) -> list:
    if key == "vaccination_type":
        col = VACCINATION_TYPE_COLUMN
    else:
        col = FILTER_TO_COLUMN[key]
    # Matches the sheet's own dropdown formulas, which exclude blank and
    # literal "NA" values (e.g. filters!A2: FILTER(..., col<>"", col<>"NA")).
    values = sorted(
        v for v in df[col].dropna().unique() if str(v).strip() not in ("", "NA")
    )
    return ["All"] + values


def apply_global_filters(
    df: pd.DataFrame,
    filters: dict,
    exclude: tuple = (),
    include_vaccination_special: bool = True,
) -> pd.DataFrame:
    """
    AND-combine every active filter except the ones in `exclude` (typically the
    page's own row dimension). The Vaccination Type filter only ever takes
    effect when Appointment Type is pinned to "Vaccination" - matching the
    sheet, where the extra AP:AP criterion only appears in that branch.
    """
    mask = pd.Series(True, index=df.index)

    for key, col in FILTER_TO_COLUMN.items():
        if key in exclude:
            continue
        val = filters.get(key, "All")
        if val and val != "All":
            mask &= df[col] == val

    if include_vaccination_special:
        vt = filters.get("vaccination_type", "All")
        if (
            vt
            and vt != "All"
            and filters.get("appointment_type") == "Vaccination"
            and "appointment_type" not in exclude
        ):
            mask &= df[VACCINATION_TYPE_COLUMN] == vt

    return df[mask]


@dataclass
class Periods:
    months: list  # [(label, start, end), ...] oldest -> newest, 4 trailing complete months
    lmtd: tuple  # (label, start, end)
    mtd: tuple  # (label, start, end)
    daily: pd.DatetimeIndex
    max_date: pd.Timestamp
    monthly_buckets: list = field(init=False)

    def __post_init__(self):
        self.monthly_buckets = [*self.months, self.lmtd, self.mtd]


def build_periods(df: pd.DataFrame, today: date | None = None) -> Periods:
    today_ts = pd.Timestamp(today or date.today())
    max_date = df["appointment_date"].max()
    if pd.isna(max_date):
        max_date = today_ts - pd.Timedelta(days=1)
    max_date = pd.Timestamp(max_date).normalize()

    months = []
    for i in range(4, 0, -1):
        m_start = today_ts.normalize().replace(day=1) - relativedelta(months=i)
        m_end = m_start + relativedelta(months=1) - pd.Timedelta(days=1)
        months.append((m_start.strftime("%b '%y"), m_start, m_end))

    lmtd_start = max_date.replace(day=1) - relativedelta(months=1)
    lmtd_end = max_date - relativedelta(months=1)
    mtd_start = max_date.replace(day=1)
    mtd_end = max_date

    daily = pd.date_range(mtd_start, mtd_end, freq="D")

    return Periods(
        months=months,
        lmtd=("LMTD", lmtd_start, lmtd_end),
        mtd=("MTD", mtd_start, mtd_end),
        daily=daily,
        max_date=max_date,
    )


def _bucket_counts(dates: pd.Series, buckets: list) -> dict:
    d = dates.dt.normalize()
    out = {}
    for label, start, end in buckets:
        out[label] = int(((d >= start) & (d <= end)).sum())
    return out


def _daily_counts(dates: pd.Series, day_range: pd.DatetimeIndex) -> dict:
    d = dates.dt.normalize()
    counts = d.value_counts()
    return {day.strftime("%d %b"): int(counts.get(day, 0)) for day in day_range}


def row_counts(subset: pd.DataFrame, periods: Periods, followup_only: bool = False) -> dict:
    pop = subset[subset["no_show"] == 0]
    if followup_only:
        pop = pop[pop["followup_app_id"].notna()]
    row = _bucket_counts(pop["appointment_date"], periods.monthly_buckets)
    row.update(_daily_counts(pop["appointment_date"], periods.daily))
    return row


def build_table(rows: list, df: pd.DataFrame, periods: Periods, followup_only: bool) -> pd.DataFrame:
    """rows: list of (label, boolean_mask) -> DataFrame indexed by label.

    Built from parallel lists (not a dict keyed by label) so rows that share a
    display label - e.g. the "without add-on service" cut repeated under each
    episode type - don't silently overwrite one another.
    """
    labels = [label for label, _ in rows]
    records = [row_counts(df[mask], periods, followup_only=followup_only) for _, mask in rows]
    return pd.DataFrame(records, index=labels)


def creation_pct_table(completed: pd.DataFrame, followups: pd.DataFrame) -> pd.DataFrame:
    denom = completed.mask(completed == 0)
    return (followups / denom) * 100


NO_ADD_ON_MASK_COLS = ("lab_imaging_flag", "procedure_flag")


def episode_type_rows(df: pd.DataFrame):
    """
    Row definitions for the Appointment Type Wise dashboard. Third element is
    the "type tag": rows tagged with a real appointment_type get hidden when
    the Appointment Type filter is pinned to a different type (matching the
    sheet's $L$3<>row-type -> 0 rule); tag None rows always show, matching
    Procedure/Diagnostic/Total, which never check that filter.
    """
    no_add_on = (df["lab_imaging_flag"] == 0) & (df["procedure_flag"] == 0)

    def type_mask(t):
        return df["appointment_type"] == t

    return [
        ("New Consultation", type_mask("New Consultation"), "New Consultation"),
        ("  ↳ New Consultation, no add-on service", type_mask("New Consultation") & no_add_on, "New Consultation"),
        ("Vaccination", type_mask("Vaccination"), "Vaccination"),
        ("  ↳ Vaccination, no add-on service", type_mask("Vaccination") & no_add_on, "Vaccination"),
        ("Follow Up", type_mask("Follow Up"), "Follow Up"),
        ("  ↳ Follow Up, no add-on service", type_mask("Follow Up") & no_add_on, "Follow Up"),
        ("Procedure (any appt. type)", df["procedure_flag"] == 1, None),
        ("Diagnostic / Imaging (any appt. type)", df["lab_imaging_flag"] == 1, None),
        ("Total (all episode types)", pd.Series(True, index=df.index), None),
    ]
