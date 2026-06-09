"""Structured logging configuration for I.N.A.Y.A.T.

Creates a single ``inayat`` logger used everywhere.  Outputs go to:
  • ``inayat_debug.log``  (file — rotating, keeps last 3 × 5 MB)
  • ``stdout``            (console — coloured by level)

Call ``setup_logging()`` once at app start; every other module simply does::

    import logging
    logger = logging.getLogger("inayat")
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

_LOGGER_NAME = "inayat"
_LOG_FILE = "inayat_debug.log"
_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%dT%H:%M:%S"


def setup_logging(
    log_level: int = logging.INFO,
    log_file: str = _LOG_FILE,
) -> logging.Logger:
    """Configure and return the application-wide logger.

    Safe to call multiple times — duplicate handlers are prevented.

    Args:
        log_level: Numeric logging level (e.g. ``logging.DEBUG``).
        log_file: Path for the debug log file.

    Returns:
        The configured ``inayat`` Logger.
    """
    logger = logging.getLogger(_LOGGER_NAME)

    # Prevent adding handlers twice (Streamlit reruns the script)
    if logger.handlers:
        return logger

    logger.setLevel(log_level)
    formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)

    # Ensure stdout/stderr don't crash on unicode characters in legacy console encodings
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except Exception:
                pass

    # ---- Console handler ----
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # ---- Rotating file handler ----
    try:
        file_h = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,   # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_h.setLevel(logging.DEBUG)   # file always captures everything
        file_h.setFormatter(formatter)
        logger.addHandler(file_h)
    except OSError as exc:
        logger.warning("Could not create log file '%s': %s", log_file, exc)

    logger.info("Logger '%s' initialised (level=%s)", _LOGGER_NAME, logging.getLevelName(log_level))
    return logger
