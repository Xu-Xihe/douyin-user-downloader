import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_log() -> logging.Logger:
    logger = logging.getLogger("main_log")
    logger.setLevel(logging.DEBUG)
    
    log = Path("log/main_log.log")
    # Mkdir log
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        logger.error(f"Make dir at path {log.parent.resolve()} failed! Permission deny.")
    # Create log file
    if not log.exists():
        try:
            log.touch()
        except PermissionError as e:
            logger.error("Create log file failed! Permission deny.")
        else:
            logger.debug("Create log file success.")
    else:
        logger.debug("Log file exist.")
    
    file_handler = RotatingFileHandler("log/main_log.log", maxBytes=1024 * 1024 * 10, backupCount=0)
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger