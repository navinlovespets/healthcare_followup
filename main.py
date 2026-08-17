import time
import platform

from logger import logger
from log_sheet import push_log

from extract import get_base_data
from transform import transform_data
from sheets import upload_to_google_sheet

from exceptions import ETLException

def main():

    start_time = time.time()

    logger.info("============================================================")
    logger.info("Healthcare Follow-up ETL Started")
    logger.info(f"Python Version : {platform.python_version()}")
    logger.info(f"Operating System : {platform.system()} {platform.release()}")
    logger.info("============================================================")

    # ======================================================
    # Extract
    # ======================================================

    df = get_base_data()

    # ======================================================
    # Transform
    # ======================================================

    base_df = transform_data(df)

    # ======================================================
    # Upload
    # ======================================================

    upload_to_google_sheet(base_df)

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Total execution time: {elapsed:.2f} seconds")

    logger.info("============================================================")
    logger.info("Healthcare Follow-up ETL Completed Successfully")
    logger.info("============================================================")

    # ======================================================
    # Push Success Log to Google Sheet
    # ======================================================

    try:

        push_log(
            status="SUCCESS",
            stage="Completed",
            message="ETL Completed Successfully",
            rows_extracted=len(df),
            rows_uploaded=len(base_df),
            duration=elapsed,
        )

    except Exception:

        logger.exception(
            "Failed to write success log to Google Sheets."
        )


if __name__ == "__main__":

    try:

        main()

    except ETLException as e:

        try:

            push_log(
                status="FAILED",
                stage=e.stage,
                message=str(e),
            )

        except Exception:

            logger.exception(
                "Failed to write failure log to Google Sheets."
            )

        logger.exception(
            f"ETL Pipeline Failed during {e.stage}."
        )

        raise

    except Exception as e:

        try:

            push_log(
                status="FAILED",
                stage="Pipeline",
                message=str(e),
            )

        except Exception:

            logger.exception(
                "Failed to write failure log to Google Sheets."
            )

        logger.exception(
            "Unexpected Pipeline Error."
        )

        raise