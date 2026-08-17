import pandas as pd
import numpy as np
import gspread
from logger import logger
from exceptions import ETLException
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1

from config import (
    SERVICE_ACCOUNT_FILE,
    SPREADSHEET_ID,
    WORKSHEET_NAME,
    SCOPES,
)

def upload_to_google_sheet(base_df):

    logger.info("========================================")
    logger.info("Starting Google Sheets upload...")
    logger.info("========================================")

    try:

        logger.info("Authenticating with Google Sheets...")

        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )

        client = gspread.authorize(creds)

        worksheet = (
            client
            .open_by_key(SPREADSHEET_ID)
            .worksheet(WORKSHEET_NAME)
        )
        logger.info("Google Sheets authentication successful.")

        # ======================================================
        # Prepare Data
        # ======================================================

        upload_df = base_df.copy()

        # ======================================================
        # Validate Data
        # ======================================================

        if upload_df.empty:

            logger.error("No data available to upload.")

            raise ValueError(
                "No data available to upload. Google Sheet was not updated."
            )

        # ======================================================
        # Convert Datetime Columns
        # ======================================================

        datetime_cols = upload_df.select_dtypes(
            include=["datetime"]
        ).columns

        for col in datetime_cols:
            upload_df[col] = upload_df[col].dt.strftime("%Y-%m-%d")

        # ======================================================
        # Convert Values
        # ======================================================

        def convert_value(value):

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

        upload_df = upload_df.map(convert_value)

        # ======================================================
        # Replace Google Sheet
        # ======================================================

        logger.info("Clearing existing Google Sheet...")

        worksheet.clear()

        # Resize sheet based on DataFrame size
        required_rows = len(upload_df) + 1000      # 1000-row buffer
        required_cols = len(upload_df.columns)

        logger.info(
            f"Resizing sheet to {required_rows} rows x {required_cols} columns..."
        )

        worksheet.resize(
            rows=required_rows,
            cols=required_cols
        )

        rows = [upload_df.columns.tolist()] + upload_df.values.tolist()

        logger.info(
            f"Uploading {len(upload_df):,} rows to Google Sheets..."
        )

        chunk_size = 1000

        # Upload Header
        worksheet.update(
            range_name="A1",
            values=[rows[0]],
            value_input_option="USER_ENTERED",
        )

        # Upload Data
        data_rows = rows[1:]

        for start in range(0, len(data_rows), chunk_size):

            end = min(start + chunk_size, len(data_rows))

            chunk = data_rows[start:end]

            start_row = start + 2
            end_row = start_row + len(chunk) - 1

            range_name = (
                f"A{start_row}:"
                f"{rowcol_to_a1(end_row, len(upload_df.columns))}"
            )

            worksheet.update(
                range_name=range_name,
                values=chunk,
                value_input_option="USER_ENTERED",
            )

            progress = (end / len(data_rows)) * 100

            logger.info(
                f"Uploaded {end:,}/{len(data_rows):,} rows "
                f"({progress:.1f}%)"
)
            
        logger.info(
                    f"Google Sheet '{WORKSHEET_NAME}' updated successfully."
                )
        logger.info(f"Rows uploaded: {len(upload_df):,}")
        logger.info(f"Columns uploaded: {len(upload_df.columns)}")
        logger.info("========================================")

    except Exception as e:

        logger.exception("Google Sheets upload failed.")

        raise ETLException(
            "Upload",
            str(e),
        )