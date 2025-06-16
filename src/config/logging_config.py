import logging
import logging.handlers
import os

LOG_FILENAME = "app.log"
LOG_LEVEL = logging.INFO  

def setup_logging():
    """
    Configures the root logger for the application.
    This setup includes:
    - A rotating file handler for detailed, persistent logs.
    - A console handler for real-time, high-level feedback (Warnings and above).
    """
    log_dir = os.path.dirname(LOG_FILENAME)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # --- File Handler (with rotation) ---
    # Creates a new log file when the current one reaches 5MB, keeping 5 old logs.
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(LOG_LEVEL) # Log everything from INFO level and up to the file
    file_formatter = logging.Formatter('%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # --- Console Handler ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO) 
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    logging.info("Logging configured. File logs will be saved to '%s'", LOG_FILENAME)