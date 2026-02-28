"""
Structured logging for observability and audit trails.
Logs are saved to files for audit and displayed on console.
"""

import logging
from datetime import datetime
from pathlib import Path
from config import BASE_DIR

# Create logs directory if it doesn't exist
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Create a unique log file for this run (with timestamp)
log_filename = f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = LOG_DIR / log_filename

# File handler - saves EVERYTHING to file (for audit trail)
file_handler = logging.FileHandler(log_filepath)
file_handler.setLevel(logging.INFO)  # Save INFO and above

# Used to print the outputs of the logs to the terminal so can be seen during a run.
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Info prints everything, Warning prints only warnings and errors, Error prints only errors

#makes logs human-readable
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Create the logger
logger = logging.getLogger("document_processor")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Log that we're starting
logger.info(f"="*70)
logger.info(f"Document Processing Pipeline Started")
logger.info(f"Log file: {log_filepath}")
logger.info(f"="*70)