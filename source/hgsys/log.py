"""Logger setup. Writes a timestamped file under ``<repo_root>/logs/`` per launch."""
import logging
import os
from datetime import datetime
from typing import Optional

LOGGER_NAME = "hgsystem"


def _default_log_dir() -> str:
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    # source/hgsys/log.py -> source/hgsys -> source -> repo root
    return os.path.abspath(os.path.join(pkg_dir, "..", "..", "logs"))


def setup_logger(log_dir: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    target = log_dir or _default_log_dir()
    os.makedirs(target, exist_ok=True)
    log_file = os.path.join(target, f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.log")

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-5.5s - %(message)s"))
    logger.addHandler(handler)
    logger.info("Start hgsystem.")
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)
