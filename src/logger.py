import logging
from rich.logging import RichHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_log() -> logging.Logger:
    # Get logger
    logger = logging.getLogger("main_log")
    logger.setLevel(logging.DEBUG)

    # Console Handler
    console_handler = RichHandler(
        level=logging.INFO,
        show_path=True,
        rich_tracebacks=True,
        enable_link_path=True,
        )
    console_handler.setFormatter(logging.Formatter("%(message)s", datefmt=r"[%X]"))
    logger.addHandler(console_handler)
    logger.info("Program Start\n")

    # Mkdir log
    log_path = Path(__file__).resolve().parent.parent / "logs/main_log.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        logger.error(f"Make dir at path {log_path.parent.resolve()} failed! Permission deny.")
    # Create log file
    if not log_path.exists():
        try:
            log_path.touch()
        except PermissionError as e:
            logger.error("Create log file failed! Permission deny.")
        else:
            logger.info("Create log file success.")
    else:
        logger.info("Log file exist.")
    
    # File Handler
    file_handler = RotatingFileHandler(str(log_path.resolve()), encoding="utf-8", maxBytes=1024 * 1024 * 10 * 5, backupCount=0)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s-%(levelname)-8s-%(filename)s:%(lineno)d-%(message)s", datefmt=r"%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    return logger