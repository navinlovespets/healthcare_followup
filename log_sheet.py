import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

from config import (
    SERVICE_ACCOUNT_FILE,
    SPREADSHEET_ID,
    SCOPES,
)

WORKSHEET_NAME = "Logs"

def push_log(
    status,
    stage,
    message,
    rows_extracted="",
    rows_uploaded="",
    duration=""
):
    """
    Append one ETL execution log to Google Sheets.
    """

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )

    client = gspread.authorize(creds)

    worksheet = (
        client
        .open_by_key(SPREADSHEET_ID)
        .worksheet(WORKSHEET_NAME)
    )

    worksheet.append_row(
        [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status,
            stage,
            rows_extracted,
            rows_uploaded,
            duration,
            message,
        ],
        value_input_option="USER_ENTERED",
    )