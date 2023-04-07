import logging
import sys


class ColorFormatter(logging.Formatter):
    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"
    FORMAT = "%(levelname)s:%(panel)s %(message)s"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: GREY + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET
    }

    def __init__(self, *args, colors: bool = True, defaults=None, **kwargs):
        self._defaults = defaults or {"panel": ""}
        self._colors = colors
        super().__init__(*args, defaults=defaults, **kwargs)

    def format(self, record):
        if sys.stderr.isatty() and self._colors:
            log_fmt = self.FORMATS.get(record.levelno)
        else:
            log_fmt = self.FORMAT
        formatter = logging.Formatter(log_fmt, defaults=self._defaults)
        return formatter.format(record)


def set_logging_formatter():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter())
    logger.addHandler(handler)
