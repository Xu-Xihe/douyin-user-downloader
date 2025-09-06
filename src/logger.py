import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def tran_log_level(level: str):
    if level == "DEBUG":
        return logging.DEBUG
    if level == "INFO":
        return logging.INFO
    if level == "WARNING":
        return logging.WARNING
    if level == "ERROR":
        return logging.ERROR
    print("Log Level Value Error.")
    sys.exit(1)

def setup_log(stream_level, file_level) -> logging.Logger:
    # Get logger
    logger = logging.getLogger("main_log")
    logger.setLevel(logging.DEBUG)

    # Make log dir
    log_path = Path(__file__).resolve().parent.parent / "data/main.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File Handler
    file_handler = TimedRotatingFileHandler(
        log_path,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setLevel(tran_log_level(file_level))
    file_handler.setFormatter(logging.Formatter("{asctime}-{levelname:^7}-{filename}-{lineno} : {message}", style="{", datefmt=r"%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

    # Stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    if stream_level == "ERROR":
        stderr_handler.setLevel(logging.ERROR)
    else:
        stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("{levelname:^7}-{filename}-{lineno}: {message}", style="{"))
    logger.addHandler(stderr_handler)

    # Stdout handler
    if not sys.stdout.isatty():
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(tran_log_level(stream_level))
        stdout_handler.setFormatter(logging.Formatter("{levelname:^7} : {message}", style="{"))
        logger.addHandler(stdout_handler)

    return logger