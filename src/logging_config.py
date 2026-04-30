import logging
import os
import sys


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = self.COLORS.get(record.levelno)
        if not color:
            return message
        return f"{color}{message}{self.RESET}"


def resolve_log_level(value: str) -> int:
    if not value:
        return logging.INFO
    normalized = value.strip()
    if not normalized:
        return logging.INFO
    if normalized.isdigit():
        return int(normalized)
    level = getattr(logging, normalized.upper(), None)
    if isinstance(level, int):
        return level
    return logging.INFO


def build_default_formatter() -> logging.Formatter:
    return logging.Formatter("%(levelname).5s [%(name)s] %(message)s")


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(resolve_log_level(os.getenv("LOG_LEVEL", "INFO")))
    root.handlers.clear()

    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(ColorFormatter("%(levelname).5s [%(name)s] %(message)s"))
    root.addHandler(console_handler)
