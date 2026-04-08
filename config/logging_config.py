import logging
import os

# create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

LOG_FILE = "logs/app.log"

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # prevent duplicate handlers
    if logger.handlers:
        return logger

    file_handler = logging.FileHandler(LOG_FILE)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger