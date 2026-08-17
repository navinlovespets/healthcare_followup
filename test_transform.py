"""
Standalone verification suite for transform.transform_data's follow-up logic.
Run directly: python3 test_transform.py
No pytest dependency - plain asserts, prints PASS/FAIL per case.
"""

import pandas as pd
import numpy as np

from transform import transform_data

FAILURES = []
PASS_COUNT = 0


def check(name, condition, detail=""):
    global PASS_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"PASS  {name}")
    else:
        FAILURES.append(name)
        print(f"FAIL  {name}  {detail}")


BASE_COLS = [
    "id", "appointment_id", "appointment_date", "appointment_type",
    "clinic", "remarks", "owner_id", "clinicId", "customer_id",
    "owner_name", "phone", "customer_segment", "vet_name",
    "patient_id", "patient_name", "global_pet_id", "patient_dob",
    "species", "breed", "gender", "sexual_status", "no_show",
    "followup_date", "followup_app_id", "followup_no_show",
    "mr_diagnosis_group", "medical_record",
]


def make_row(**kwargs):
    row = {c: None for c in BASE_COLS}
    row.update({
        "no_show": 0,
        "followup_app_id": np.nan,
        "followup_date": pd.NaT,
        "medical_record": None,
        "appointment_type": "Consultation",
        "clinic": "C1",
        "clinicId": 1,
    })
    row.update(kwargs)
    return row


def run(rows):
    df = pd.DataFrame(rows)
    return transform_data(df)


def get(out, appointment_id):
    r = out[out["appointment_id"] == appointment_id]
    assert len(r) == 1, f"expected exactly 1 row for id={appointment_id}, got {len(r)}"
    return r.iloc[0]


# ======================================================
# Case A: No follow-up created (eligible initial appointment)
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0),
])
r = get(out, 1)
check("A: no followup_app_id -> follow_up_success = 0",
      r["follow_up_success"] == 0, r["follow_up_success"])
check("A: reason = 'Follow-up not created'",
      r["return_reason"] == "Follow-up not created", r["return_reason"])
check("A: actual_return_id blank",
      pd.isna(r["actual_return_id"]))


# ======================================================
# Case B: Planned follow-up attended
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0, followup_app_id=2),
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=0),
])
r = get(out, 1)
check("B: planned followup attended -> success = 1",
      r["follow_up_success"] == 1, r["follow_up_success"])
check("B: reason = 'Planned follow-up attended'",
      r["return_reason"] == "Planned follow-up attended", r["return_reason"])
check("B: actual_return_id = followup appointment id",
      r["actual_return_id"] == 2, r["actual_return_id"])
check("B: actual_return_date = followup's actual date",
      pd.Timestamp(r["actual_return_date"]) == pd.Timestamp("2026-08-10"))
check("B: return_days = 9",
      r["return_days"] == 9, r["return_days"])


# ======================================================
# Case C: No-show planned follow-up, valid return found
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0, followup_app_id=2),
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=1),  # planned followup, no-show
    make_row(id=3, appointment_id=3, patient_id="P1",
              appointment_date="2026-08-12", no_show=0),  # actual return
])
r = get(out, 1)
check("C: no-show + return found -> success = 1",
      r["follow_up_success"] == 1, r["follow_up_success"])
check("C: reason = 'Returned in follow-up window'",
      r["return_reason"] == "Returned in follow-up window", r["return_reason"])
check("C: actual_return_id = 3",
      r["actual_return_id"] == 3, r["actual_return_id"])
check("C: return_days = 11 (from original appointment)",
      r["return_days"] == 11, r["return_days"])


# ======================================================
# Case D: No-show planned follow-up, no valid return
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0, followup_app_id=2),
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=1),
])
r = get(out, 1)
check("D: no-show + no return -> success = 0",
      r["follow_up_success"] == 0, r["follow_up_success"])
check("D: reason = 'No return'",
      r["return_reason"] == "No return", r["return_reason"])
check("D: actual_return_id blank",
      pd.isna(r["actual_return_id"]))


# ======================================================
# Case E: Initial appointment itself is a no-show -> excluded (blank)
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=1, followup_app_id=2),
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=0),
])
r = get(out, 1)
check("E: initial no-show -> follow_up_success stays <NA>",
      pd.isna(r["follow_up_success"]), r["follow_up_success"])
check("E: reason = 'Initial appointment no-show'",
      r["return_reason"] == "Initial appointment no-show", r["return_reason"])


# ======================================================
# Case F: followup_app_id points to a non-existent appointment
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0, followup_app_id=999),
])
r = get(out, 1)
check("F: unresolved followup_app_id -> success = 0",
      r["follow_up_success"] == 0, r["follow_up_success"])
check("F: reason = 'Follow-up appointment not found'",
      r["return_reason"] == "Follow-up appointment not found", r["return_reason"])


# ======================================================
# Case G: Date window boundaries (planned followup date = 10-Aug)
# window should be [08-Aug, 17-Aug] inclusive, anchored on the
# planned follow-up appointment's ACTUAL date (id=2's own date).
# ======================================================
def window_case(candidate_date, candidate_id=3):
    rows = [
        make_row(id=1, appointment_id=1, patient_id="P1",
                  appointment_date="2026-08-01", no_show=0, followup_app_id=2),
        make_row(id=2, appointment_id=2, patient_id="P1",
                  appointment_date="2026-08-10", no_show=1),
        make_row(id=candidate_id, appointment_id=candidate_id, patient_id="P1",
                  appointment_date=candidate_date, no_show=0),
    ]
    out = run(rows)
    return get(out, 1)

r = window_case("2026-08-07")
check("G: 07-Aug (before window) -> NOT a qualifying return",
      r["follow_up_success"] == 0 and pd.isna(r["actual_return_id"]),
      (r["follow_up_success"], r["actual_return_id"]))

r = window_case("2026-08-08")
check("G: 08-Aug (lower bound, inclusive) -> qualifies",
      r["follow_up_success"] == 1 and r["actual_return_id"] == 3)

r = window_case("2026-08-17")
check("G: 17-Aug (upper bound, inclusive) -> qualifies",
      r["follow_up_success"] == 1 and r["actual_return_id"] == 3)

r = window_case("2026-08-18")
check("G: 18-Aug (after window) -> NOT a qualifying return",
      r["follow_up_success"] == 0 and pd.isna(r["actual_return_id"]))


# ======================================================
# Case H: excluded appointment types are skipped in return search
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0, followup_app_id=2),
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=1),
    make_row(id=3, appointment_id=3, patient_id="P1",
              appointment_date="2026-08-11", no_show=0, appointment_type="Grooming"),
    make_row(id=4, appointment_id=4, patient_id="P1",
              appointment_date="2026-08-13", no_show=0, appointment_type="Other"),
    make_row(id=5, appointment_id=5, patient_id="P1",
              appointment_date="2026-08-15", no_show=0, appointment_type="Consultation"),
])
r = get(out, 1)
check("H: Grooming/Other skipped, first valid Consultation picked",
      r["actual_return_id"] == 5, r["actual_return_id"])


# ======================================================
# Case I: earliest qualifying visit picked even if before planned date
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0, followup_app_id=2),
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=1),
    make_row(id=3, appointment_id=3, patient_id="P1",
              appointment_date="2026-08-09", no_show=0),  # earlier, in window
    make_row(id=4, appointment_id=4, patient_id="P1",
              appointment_date="2026-08-12", no_show=0),  # later, in window
])
r = get(out, 1)
check("I: earliest qualifying visit selected (08-09 over 08-12)",
      r["actual_return_id"] == 3, r["actual_return_id"])


# ======================================================
# Case J: original appointment and planned-followup appointment excluded
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-10", no_show=0, followup_app_id=1),  # self-reference edge
])
r = get(out, 1)
check("J: self-referencing followup_app_id does not crash and resolves",
      r["follow_up_success"] in (0, 1), r["follow_up_success"])


# ======================================================
# Case K: duplicate appointment_id rows are de-duplicated
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0),
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0),
])
check("K: duplicate appointment_id collapsed to 1 row",
      len(out) == 1, len(out))
check("K: appointment_id is unique in output",
      out["appointment_id"].is_unique)


# ======================================================
# Case L: different patient's visit in same window is NOT counted
# ======================================================
out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0, followup_app_id=2),
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=1),
    make_row(id=3, appointment_id=3, patient_id="P2",
              appointment_date="2026-08-11", no_show=0),  # different patient
])
r = get(out, 1)
check("L: other patient's visit not counted as a return",
      r["follow_up_success"] == 0 and pd.isna(r["actual_return_id"]))


# ======================================================
# Case M: no duplicate appointment_id in a larger mixed dataset
# ======================================================
rows = []
for i in range(1, 21):
    rows.append(make_row(
        id=i, appointment_id=i, patient_id=f"P{i % 3}",
        appointment_date=f"2026-08-{(i % 27) + 1:02d}",
        no_show=i % 4 == 0,
        followup_app_id=(i + 1) if i < 20 else np.nan,
    ))
out = run(rows)
check("M: no duplicate appointment_id across full run",
      out["appointment_id"].is_unique)
check("M: row count preserved (no silent drops)",
      len(out) == 20, len(out))


# ======================================================
# Case N: values survive sheets.py's DataFrame.map conversion as
# clean native int (not float) for real values, "" for blanks.
# Guards against the pandas "Int64" -> float64 upcast that
# DataFrame.map applies to nullable-integer extension columns.
# ======================================================
def sheets_convert_value(value):
    if pd.isna(value):
        return ""
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return value


out = run([
    make_row(id=1, appointment_id=1, patient_id="P1",
              appointment_date="2026-08-01", no_show=0),  # eligible, no followup -> 0
    make_row(id=2, appointment_id=2, patient_id="P1",
              appointment_date="2026-08-10", no_show=1, followup_app_id=1),  # excluded -> blank
])
upload_df = out.copy()
for col in upload_df.select_dtypes(include=["datetime"]).columns:
    upload_df[col] = upload_df[col].dt.strftime("%Y-%m-%d")
upload_df = upload_df.map(sheets_convert_value)

check("N: eligible zero renders as native int 0 (not 0.0/float)",
      upload_df.iloc[0]["follow_up_success"] == 0
      and isinstance(upload_df.iloc[0]["follow_up_success"], int)
      and not isinstance(upload_df.iloc[0]["follow_up_success"], bool),
      (upload_df.iloc[0]["follow_up_success"], type(upload_df.iloc[0]["follow_up_success"])))

check("N: excluded row renders as blank string, not 'nan'/NaN",
      upload_df.iloc[1]["follow_up_success"] == "",
      upload_df.iloc[1]["follow_up_success"])


# ======================================================
# Summary
# ======================================================
print()
print(f"{PASS_COUNT} passed, {len(FAILURES)} failed")
if FAILURES:
    print("FAILED CASES:")
    for f in FAILURES:
        print(" -", f)
    raise SystemExit(1)
