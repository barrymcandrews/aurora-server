import sys
import logging

setup_loggers = []


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if name not in setup_loggers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        setup_loggers.append(name)
    logger.setLevel(logging.DEBUG)
    return logger
