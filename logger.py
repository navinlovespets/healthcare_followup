import logging

# ======================================================
# Logger Configuration
# ======================================================

logger = logging.getLogger("healthcare_etl")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not logger.handlers:

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --------------------------------------------------
    # Console Handler
    # --------------------------------------------------

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # --------------------------------------------------
    # Add Handlers
    # --------------------------------------------------

    logger.addHandler(console_handler)

    # Prevent logs from propagating to root logger
    logger.propagate = False