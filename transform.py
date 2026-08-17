import json
import re
from exceptions import ETLException
import pandas as pd
import numpy as np
from logger import logger

# ======================================================
# Age Group
# ======================================================

def get_age_group(age):

    if pd.isna(age):
        return "Unknown"

    if age < 0.25:
        return "0-3 Months"

    elif age < 0.5:
        return "3-6 Months"

    elif age < 1:
        return "6-12 Months"

    elif age < 3:
        return "1-3 Years"

    elif age < 7:
        return "3-7 Years"

    return ">7 Years"

# ======================================================
# Vaccine Regex Patterns
# ======================================================

DOG_CORE = re.compile(
    r"Nobivac DHPPiL4|Nobivac DHPPi|Nobivac\s*7\s*-?in-?\s*1|Vanguard 5 L4|Vanguard DAPP|Vanguard Plus 5 L4|DHPP|DHPPi|DHP",
    re.IGNORECASE,
)

LEPTO = re.compile(
    r"Lepto Vaccine|Nobivac Lepto|Nobivac\s*7\s*-?in-?\s*1",
    re.IGNORECASE,
)

CAT_CORE = re.compile(
    r"Tricat|Felocell|FVRCP|CRP Vaccine",
    re.IGNORECASE,
)

RABIES = re.compile(
    r"ARV|Defensor|Rabies",
    re.IGNORECASE,
)

KENNEL_COUGH = re.compile(
    r"Kennel Cough|Nobivac KC|KC Vaccine",
    re.IGNORECASE,
)

POST_BITE = re.compile(
    r"Post Bite ARV",
    re.IGNORECASE,
)

CORONAVIRUS = re.compile(
    r"Vanguard CV|Canine Coronavirus|CCV Vaccine",
    re.IGNORECASE,
)

# ======================================================
# Vaccine Category
# ======================================================

def vaccine_category(vaccine):

    if pd.isna(vaccine) or str(vaccine).strip() == "":
        return ""

    vaccine = str(vaccine)

    categories = []

    if DOG_CORE.search(vaccine):
        categories.append("Dog Core")

    if LEPTO.search(vaccine):
        categories.append("Lepto")

    if CAT_CORE.search(vaccine):
        categories.append("Cat Core")

    if RABIES.search(vaccine):
        categories.append("Rabies")

    if KENNEL_COUGH.search(vaccine):
        categories.append("Kennel Cough")

    if POST_BITE.search(vaccine):
        categories.append("Post Bite ARV")

    if CORONAVIRUS.search(vaccine):
        categories.append("Canine Coronavirus")

    return ", ".join(categories) if categories else "Unclassified"

# ======================================================
# Vaccination Extraction
# ======================================================

def extract_vaccine_names(record):
    """
    Extract vaccine names from medical_record JSON.
    """

    try:

        if pd.isna(record):
            return None

        if isinstance(record, str):
            record = json.loads(record)

        vaccinations = record.get("vaccinations")

        if not vaccinations:
            return None

        vaccine_names = []

        def find_vaccines(obj):

            if isinstance(obj, dict):

                if obj.get("vaccine_name"):
                    vaccine_names.append(obj["vaccine_name"])

                for value in obj.values():
                    find_vaccines(value)

            elif isinstance(obj, list):

                for item in obj:
                    find_vaccines(item)

        find_vaccines(vaccinations)

        vaccine_names = list(dict.fromkeys(vaccine_names))

        return ", ".join(vaccine_names) if vaccine_names else None

    except Exception:
        return None

# ======================================================
# Medical Record Extraction
# ======================================================

def extract_medical_record(record):
    """
    Extract procedure, laboratory and imaging details
    from medical_record JSON.
    """

    procedure_names = None
    lab_test_names = None
    imaging_names = None
    lab_imaging_flag = 0
    procedure_flag = 0

    if pd.isna(record):
        return pd.Series([
            procedure_names,
            lab_test_names,
            imaging_names,
            lab_imaging_flag,
            procedure_flag
        ])

    try:

        data = json.loads(record) if isinstance(record, str) else record

        # -------------------------
        # Procedure
        # -------------------------

        procedures = data.get("procedure")

        if procedures:

            names = []

            for group in procedures:

                if isinstance(group, list):

                    for item in group:

                        if item.get("name"):
                            names.append(item["name"])

                elif isinstance(group, dict):

                    if group.get("name"):
                        names.append(group["name"])

            if names:
                procedure_names = ", ".join(sorted(set(names)))
                procedure_flag = 1

        # -------------------------
        # Laboratory Tests
        # -------------------------

        lab_tests = data.get("laboratory_tests")

        if lab_tests:

            names = []

            for group in lab_tests:

                if isinstance(group, list):

                    for item in group:

                        if item.get("test_name"):
                            names.append(item["test_name"])

                elif isinstance(group, dict):

                    if group.get("test_name"):
                        names.append(group["test_name"])

            if names:
                lab_test_names = ", ".join(sorted(set(names)))
                lab_imaging_flag = 1

        # -------------------------
        # Imaging
        # -------------------------

        imaging = data.get("imaging")

        if imaging:

            names = []

            for group in imaging:

                if isinstance(group, list):

                    for item in group:

                        if item.get("test_name"):
                            names.append(item["test_name"])

                elif isinstance(group, dict):

                    if group.get("test_name"):
                        names.append(group["test_name"])

            if names:
                imaging_names = ", ".join(sorted(set(names)))
                lab_imaging_flag = 1

    except Exception:
        pass

    return pd.Series([
        procedure_names,
        lab_test_names,
        imaging_names,
        lab_imaging_flag,
        procedure_flag,
    ])

# ======================================================
# Main Transformation
# ======================================================
def transform_data(df):
    """
    Transform raw clinic appointment data into BASE_DATA.
    """

    logger.info("========================================")
    logger.info("Starting data transformation...")
    logger.info("========================================")

    try:

        # ======================================================
        # STEP 1 : Data Preparation
        # ======================================================
        logger.info("[STEP 1/9] Preparing appointment data...")

        df["appointment_date"] = pd.to_datetime(
            df["appointment_date"],
            errors="coerce",
        )

        df["followup_date"] = pd.to_datetime(
            df["followup_date"],
            errors="coerce",
        )
        df["appointment_id"] = pd.to_numeric(df["appointment_id"], errors="coerce")
        df["followup_app_id"] = pd.to_numeric(df["followup_app_id"], errors="coerce")
        df["no_show"] = pd.to_numeric(df["no_show"], errors="coerce")

        # Dashboards filter on species directly from the source; a blank
        # value there is indistinguishable from "no filter selected" in a
        # COUNTIFS-style "All" criteria, so those rows get silently dropped.
        # Never leave it blank.
        df["species"] = df["species"].fillna("Unknown")
        df.loc[df["species"].astype(str).str.strip() == "", "species"] = "Unknown"

        # Same reasoning for mr_diagnosis_group - it's legitimately blank for
        # a large share of visits (e.g. routine vaccination/grooming with no
        # diagnosis recorded), but a dashboard "All" filter must still be
        # able to include those rows rather than silently drop them.
        df["mr_diagnosis_group"] = df["mr_diagnosis_group"].fillna("Not Applicable")
        df.loc[df["mr_diagnosis_group"].astype(str).str.strip() == "", "mr_diagnosis_group"] = "Not Applicable"

        # --------------------------------------------------
        # Drop rows with no appointment_id - they can never be
        # matched as a follow-up target and would corrupt the
        # merge/lookup below.
        # --------------------------------------------------

        missing_id_count = df["appointment_id"].isna().sum()

        if missing_id_count:

            logger.warning(
                f"Dropping {missing_id_count:,} row(s) with missing appointment_id."
            )

            df = df[df["appointment_id"].notna()]

        # --------------------------------------------------
        # De-duplicate on appointment_id so every appointment
        # is represented exactly once. Duplicates would fan out
        # the follow-up lookup merge and double count rows on
        # the dashboard.
        # --------------------------------------------------

        duplicate_count = df["appointment_id"].duplicated().sum()

        if duplicate_count:

            logger.warning(
                f"Dropping {duplicate_count:,} duplicate appointment_id row(s), "
                "keeping first occurrence."
            )

            df = df.drop_duplicates(subset="appointment_id", keep="first")

        logger.info("[STEP 1/9] Appointment data prepared.")
        # ======================================================
        # STEP 2 : Medical Record Extraction
        # ======================================================

        logger.info("[STEP 2/9] Extracting medical record details...")

        df[
            [
                "procedure_name",
                "lab_test_name",
                "imaging_test_name",
                "lab_imaging_flag",
                "procedure_flag",
            ]
        ] = df["medical_record"].apply(extract_medical_record)

        logger.info("[STEP 2/9] Medical record extraction completed.")

        # ======================================================
        # STEP 3 : Follow-up Processing
        # ======================================================
        logger.info("[STEP 3/9] Preparing follow-up history...")

        appointment_history = (
            df
            .sort_values(
                ["patient_id", "appointment_date"]
            )
            .reset_index(drop=True)
        )

        followup_lookup = (
            appointment_history[
                [
                    "appointment_id",
                    "appointment_date",
                    "appointment_type",
                    "no_show",
                ]
            ]
            .rename(
                columns={
                    "appointment_id": "followup_id",
                    "appointment_date": "planned_followup_actual_date",
                    "appointment_type": "planned_followup_type",
                    "no_show": "planned_followup_no_show",
                }
            )
        )

        base_df = appointment_history.merge(
            followup_lookup,
            left_on="followup_app_id",
            right_on="followup_id",
            how="left",
        )

        # Safety net: a clean 1:1 followup_id lookup must never fan out
        # the merge. If it did, something upstream produced duplicate
        # appointment_ids that slipped past the STEP 1 de-duplication.
        if len(base_df) != len(appointment_history):

            raise ETLException(
                "Transform",
                "Follow-up lookup merge changed row count "
                f"({len(appointment_history):,} -> {len(base_df):,}); "
                "check for duplicate appointment_id values.",
            )

        logger.info("[STEP 3/9] Follow-up history prepared.")

        # ======================================================
        # STEP 4 : Initialize Output Columns
        # ======================================================
        logger.info("[STEP 4/9] Initializing output columns...")

        # Plain-Python-int object columns (not pandas "Int64") for
        # follow_up_success/actual_return_id/return_days. The Google
        # Sheets upload step (sheets.py) runs DataFrame.map over the
        # output, which silently upcasts nullable Int64 columns to
        # float64 (0 -> 0.0) when pulling out scalars. Object columns
        # holding native Python int / np.nan survive that call intact,
        # so "no data" (NaN -> blank cell) and the real value "0" stay
        # distinguishable and render as clean integers on the sheet.
        base_df["follow_up_success"] = pd.Series(
            np.nan, index=base_df.index, dtype="object"
        )
        base_df["return_reason"] = ""

        base_df["actual_return_id"] = pd.Series(
            np.nan, index=base_df.index, dtype="object"
        )
        base_df["actual_return_date"] = pd.Series(
            pd.NaT, index=base_df.index, dtype="datetime64[ns]"
        )
        base_df["actual_return_type"] = ""
        base_df["return_days"] = pd.Series(
            np.nan, index=base_df.index, dtype="object"
        )

        excluded = [
            "Other",
            "Grooming",
        ]
        logger.info("[STEP 4/9] Output columns initialized.")

        # ======================================================
        # STEP 5 : Follow-up Success Logic
        # ======================================================
        logger.info("[STEP 5/9] Calculating follow-up success...")
        for idx, row in base_df.iterrows():

            # --------------------------------------------------
            # Rule 0: initial appointment itself was a no-show.
            # It never happened, so it cannot anchor a follow-up
            # and must be excluded from the success denominator
            # entirely (follow_up_success stays <NA>, not 0/1).
            # --------------------------------------------------
            if pd.isna(row["no_show"]) or row["no_show"] != 0:

                base_df.at[idx, "return_reason"] = "Initial appointment no-show"
                continue

            # --------------------------------------------------
            # Rule 1: no follow-up was ever scheduled.
            # --------------------------------------------------
            if pd.isna(row["followup_app_id"]):

                base_df.at[idx, "follow_up_success"] = 0
                base_df.at[idx, "return_reason"] = "Follow-up not created"
                continue

            # --------------------------------------------------
            # Rule 2: followup_app_id does not resolve to a real
            # appointment record (bad reference / outside extract
            # window). Do not silently fall through to a return
            # search anchored on nothing.
            # --------------------------------------------------
            if pd.isna(row["planned_followup_no_show"]):

                base_df.at[idx, "follow_up_success"] = 0
                base_df.at[idx, "return_reason"] = "Follow-up appointment not found"
                continue

            # Anchor every downstream date check on the follow-up
            # appointment's own actual date, not the (possibly stale)
            # originally-scheduled followup_date field.
            anchor_date = row["planned_followup_actual_date"]

            # --------------------------------------------------
            # Rule 3: planned follow-up was attended.
            # --------------------------------------------------
            if row["planned_followup_no_show"] == 0:

                base_df.at[idx, "follow_up_success"] = 1
                base_df.at[idx, "return_reason"] = "Planned follow-up attended"

                base_df.at[idx, "actual_return_id"] = int(row["followup_app_id"])
                base_df.at[idx, "actual_return_date"] = anchor_date
                base_df.at[idx, "actual_return_type"] = row["planned_followup_type"]
                base_df.at[idx, "return_days"] = int(
                    (anchor_date - row["appointment_date"]).days
                )

                continue

            # --------------------------------------------------
            # Rule 4: planned follow-up was a no-show. Search for
            # any other qualifying visit by the same patient in
            # the window [anchor_date - 2, anchor_date + 7].
            # --------------------------------------------------
            visits = appointment_history[
                (
                    appointment_history["patient_id"]
                    == row["patient_id"]
                )
                &
                (
                    appointment_history["appointment_date"]
                    >= anchor_date - pd.Timedelta(days=2)
                )
                &
                (
                    appointment_history["appointment_date"]
                    <= anchor_date + pd.Timedelta(days=7)
                )
                &
                (
                    ~appointment_history["appointment_type"].isin(excluded)
                )
            ].copy()

            # Ignore original appointment
            visits = visits[
                visits["appointment_id"]
                != row["appointment_id"]
            ]

            # Ignore planned follow-up itself
            visits = visits[
                visits["appointment_id"]
                != row["followup_app_id"]
            ]

            # Only completed visits
            visits = visits[
                visits["no_show"] == 0
            ]

            if not visits.empty:

                # Earliest qualifying visit; tie-break on appointment_id
                # so the pick is deterministic when two visits share a date.
                visit = (
                    visits
                    .sort_values(["appointment_date", "appointment_id"])
                    .iloc[0]
                )

                base_df.at[idx, "follow_up_success"] = 1
                base_df.at[idx, "return_reason"] = "Returned in follow-up window"

                base_df.at[idx, "actual_return_id"] = int(visit["appointment_id"])
                base_df.at[idx, "actual_return_date"] = visit["appointment_date"]
                base_df.at[idx, "actual_return_type"] = visit["appointment_type"]
                base_df.at[idx, "return_days"] = int(
                    (visit["appointment_date"] - row["appointment_date"]).days
                )

            else:

                base_df.at[idx, "follow_up_success"] = 0
                base_df.at[idx, "return_reason"] = "No return"

        logger.info("[STEP 5/9] Follow-up success calculation completed.")

        # --------------------------------------------------
        # Final reliability guard: appointment_id must be unique
        # in the output that goes to the dashboard.
        # --------------------------------------------------
        if not base_df["appointment_id"].is_unique:

            dup_count = base_df["appointment_id"].duplicated().sum()

            raise ETLException(
                "Transform",
                f"Output contains {dup_count:,} duplicate appointment_id row(s) "
                "after follow-up processing.",
            )

        # ======================================================
        # STEP 6 : Vaccination Extraction
        # ======================================================
        logger.info("[STEP 6/9] Extracting vaccination details...")

        base_df["vaccination_name"] = (
            base_df["medical_record"]
            .apply(extract_vaccine_names)
        )
        logger.info("[STEP 6/9] Vaccination extraction completed.")

        # ======================================================
        # STEP 7 : Age Calculation
        # ======================================================
        logger.info("[STEP 7/9] Calculating patient age...")

        base_df["appointment_date"] = pd.to_datetime(
            base_df["appointment_date"],
            errors="coerce",
        )

        base_df["patient_dob"] = pd.to_datetime(
            base_df["patient_dob"],
            errors="coerce",
        )

        base_df["patient_age_apt_based"] = (
            (
                base_df["appointment_date"]
                - base_df["patient_dob"]
            ).dt.days
            / 365.25
        ).round(2)

        base_df["age_group"] = (
            base_df["patient_age_apt_based"]
            .apply(get_age_group)
        )
        logger.info("[STEP 7/9] Age calculation completed.")

        # ======================================================
        # STEP 8 : Vaccination Category
        # ======================================================
        logger.info("[STEP 8/9] Categorizing vaccinations...")

        base_df["vaccination_category"] = (
            base_df["vaccination_name"]
            .fillna("")
            .apply(vaccine_category)
        )

        # A completed "Vaccination" appointment should never leave
        # vaccination_category blank, even when medical_record has no
        # recognizable vaccine name - a blank here is indistinguishable from
        # "not a vaccination visit at all" to any downstream "All" filter on
        # this field. Only applies to no_show=0: nothing was administered on
        # a missed appointment, so there is nothing to classify.
        base_df.loc[
            (base_df["vaccination_category"] == "")
            & (base_df["appointment_type"] == "Vaccination")
            & (base_df["no_show"] == 0),
            "vaccination_category",
        ] = "Unclassified"

        base_df["Combined"] = np.where(
            (
                (base_df["vaccination_category"] == "")
                |
                (base_df["age_group"] == "")
            ),
            "",
            base_df["vaccination_category"]
            + " | "
            + base_df["age_group"],
        )
        logger.info("[STEP 8/9] Vaccination categorization completed.")

        # ======================================================
        # STEP 9 : Final Output
        # ======================================================
        logger.info("[STEP 9/9] Preparing final output dataset...")

        base_df["data_source"] = "python_processing"

        final_columns = [
            "id",
            "appointment_id",
            "appointment_date",
            "appointment_type",
            "data_source",
            "clinic",
            "remarks",
            "owner_id",
            "clinicId",
            "customer_id",
            "owner_name",
            "phone",
            "customer_segment",
            "vet_name",
            "patient_id",
            "patient_name",
            "global_pet_id",
            "patient_dob",
            "patient_age_apt_based",
            "species",
            "breed",
            "gender",
            "sexual_status",
            "no_show",
            "followup_date",
            "followup_app_id",
            "followup_no_show",
            "mr_diagnosis_group",
            "medical_record",
            "followup_id",
            "planned_followup_actual_date",
            "planned_followup_type",
            "planned_followup_no_show",
            "actual_return_id",
            "actual_return_date",
            "actual_return_type",
            "follow_up_success",
            "return_reason",
            "vaccination_category",
            "vaccination_name",
            "age_group",
            "Combined",
            "procedure_name",
            "lab_test_name",
            "imaging_test_name",
            "lab_imaging_flag",
            "procedure_flag",
            "return_days",
        ]

        base_df = base_df[final_columns]
        logger.info("[STEP 9/9] Final output dataset prepared.")

        logger.info(f"Transformation completed successfully. Output rows: {len(base_df):,}")
        logger.info("========================================")

        return base_df



    except Exception as e:

        logger.exception("Transformation failed.")

        raise ETLException(
            "Transform",
            str(e),
        )
