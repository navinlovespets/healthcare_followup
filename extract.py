from sqlalchemy import create_engine
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

from exceptions import ETLException
from config import *
from logger import logger

# ======================================================
# MYSQL CONNECTION
# ======================================================

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    pool_pre_ping=True,
    echo=False,
)

# ======================================================
# EXTRACT DATA
# ======================================================

def get_base_data():

    logger.info("Starting data extraction from MySQL...")

    # ======================================================
    # Dynamic Start Date
    # First day of the month 4 months before the current month,
    # so the extract always covers the last 4 complete months
    # plus the current month to date. Rolls over the year
    # boundary automatically.
    # Example:
    # Today = 13-Aug-2026 -> start_date = 01-Apr-2026
    #         (Apr, May, Jun, Jul full + Aug MTD)
    # Today = 03-Sep-2026 -> start_date = 01-May-2026
    #         (May, Jun, Jul, Aug full + Sep MTD)
    # ======================================================

    today = date.today()

    start_date = today.replace(day=1) - relativedelta(months=4)

    logger.info(f"Extracting data from: {start_date} to Yesterday")

    query = f"""
    SELECT *
    FROM healthcare.clinic_appointments
    WHERE DATE(appointment_date)
    BETWEEN '{start_date}'
    AND DATE_SUB(CURDATE(), INTERVAL 1 DAY)
    """

    try:

        # Force a database connection
        with engine.connect():
            logger.info("Connected to MySQL successfully.")

        df = pd.read_sql(query, engine)

        logger.info(f"Successfully extracted {len(df):,} rows.")

        return df

    except Exception as e:

        logger.exception("Failed to extract data from MySQL.")

        raise ETLException(
            "Extract",
            str(e),
        )