from dotenv import load_dotenv
import os

# ======================================================
# LOAD ENVIRONMENT VARIABLES
# ======================================================

load_dotenv()

# ======================================================
# DATABASE CONFIGURATION
# ======================================================

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = rf"{os.getenv('DB_PASSWORD')}"
DB_HOST = os.getenv("DB_HOST")

DB_PORT_RAW = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# ======================================================
# GOOGLE SHEETS CONFIGURATION
# ======================================================

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

# ======================================================
# VALIDATE REQUIRED CONFIGURATION
# ======================================================

required_config = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT_RAW,
    "DB_NAME": DB_NAME,
    "SPREADSHEET_ID": SPREADSHEET_ID,
    "WORKSHEET_NAME": WORKSHEET_NAME,
    "SERVICE_ACCOUNT_FILE": SERVICE_ACCOUNT_FILE,
}

missing = [
    key
    for key, value in required_config.items()
    if value in (None, "")
]

if missing:
    raise ValueError(
        "Missing required environment variables: "
        + ", ".join(missing)
    )

# ======================================================
# TYPE CONVERSIONS
# ======================================================

DB_PORT = int(DB_PORT_RAW)