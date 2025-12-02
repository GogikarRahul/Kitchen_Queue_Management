import logging
from logging.handlers import RotatingFileHandler
import os

LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# -----------------------
# BASIC FORMATTERS
# -----------------------
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] — %(message)s",
    "%Y-%m-%d %H:%M:%S",
)

error_formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] — %(message)s (%(pathname)s:%(lineno)d)",
    "%Y-%m-%d %H:%M:%S",
)

# -----------------------
# LOG FILE HANDLERS
# -----------------------
app_handler = RotatingFileHandler(
    f"{LOGS_DIR}/app.log",
    maxBytes=2 * 1024 * 1024,
    backupCount=5,
)
app_handler.setFormatter(formatter)
app_handler.setLevel(logging.INFO)

error_handler = RotatingFileHandler(
    f"{LOGS_DIR}/error.log",
    maxBytes=2 * 1024 * 1024,
    backupCount=5,
)
error_handler.setFormatter(error_formatter)
error_handler.setLevel(logging.ERROR)

# -----------------------
# CONSOLE HANDLER (FIXED!)
# -----------------------
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# -----------------------
# CORE LOGGER
# -----------------------
logger = logging.getLogger("kitchen_queue")
logger.setLevel(logging.INFO)
logger.addHandler(app_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)

logger.propagate = False


def get_logger(name: str):
    return logger.getChild(name)
