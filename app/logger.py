import os
import logging
from logging.handlers import RotatingFileHandler

# Create a logs directory if it doesn't exist
LOGS_DIR = os.environ.get("LOGS_DIR", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Set up logger
logger = logging.getLogger("text_app_logger")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    os.path.join(LOGS_DIR, "text_app.log"), 
    maxBytes=5*1024*1024, 
    backupCount=3
)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Optional console logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info(f"Logger initialized, logs directory: {LOGS_DIR}")
