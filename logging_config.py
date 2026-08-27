import logging
import sys

LOG_FILE = "run.log"
_configured_loggers = set()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if name in _configured_loggers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File logging only works on a writable filesystem. Serverless platforms
    # like Vercel ship a read-only filesystem (except /tmp), so skip the file
    # handler there instead of crashing the whole import.
    try:
        file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        pass

    _configured_loggers.add(name)
    return logger
