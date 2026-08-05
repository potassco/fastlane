"""
Setup project wide loggers.
"""

import logging
import sys

DEBUG_EXTRA = 5
logging.addLevelName(DEBUG_EXTRA, "DEBUG_EXTRA")


class LNSLogger(logging.Logger):
    """
    Logger with an additional DEBUG_EXTRA level method.
    """

    def debug_extra(self, message: object, *args: object, **kwargs: object) -> None:  # nocoverage
        """
        Log a message with level DEBUG_EXTRA.

        :param message: The message to log.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        if self.isEnabledFor(DEBUG_EXTRA):
            self.log(DEBUG_EXTRA, message, *args, **kwargs)  # type: ignore[arg-type]


logging.setLoggerClass(LNSLogger)

COLORS = {
    "GREY": "\033[90m",
    "BLUE": "\033[94m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "NORMAL": "\033[0m",
}


class SingleLevelFilter(logging.Filter):
    """
    Filter levels.
    """

    def __init__(self, passlevel: int, reject: bool) -> None:
        # pylint: disable=super-init-not-called
        self.passlevel = passlevel
        self.reject = reject

    def filter(self, record: logging.LogRecord) -> bool:
        if self.reject:
            return record.levelno != self.passlevel  # nocoverage

        return record.levelno == self.passlevel


def setup_logger(name: str, level: int) -> LNSLogger:
    """
    Setup logger.
    """

    logger = logging.getLogger(name)
    assert isinstance(logger, LNSLogger)

    # Avoid duplicate handlers when setup is called repeatedly with the same logger name.
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(level)
    log_message_str = "{}%(levelname)s:{}  - %(message)s{}"

    def set_handler(level: int, color: str) -> None:
        handler = logging.StreamHandler(sys.stderr)
        handler.addFilter(SingleLevelFilter(level, False))
        handler.setLevel(level)
        formatter = logging.Formatter(log_message_str.format(COLORS[color], COLORS["GREY"], COLORS["NORMAL"]))
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    set_handler(logging.INFO, "GREEN")
    set_handler(logging.WARNING, "YELLOW")
    set_handler(logging.DEBUG, "BLUE")
    set_handler(DEBUG_EXTRA, "BLUE")
    set_handler(logging.ERROR, "RED")

    return logger
