import logging

from app.logging_config import configure_logging


def setup_logger() -> None:
    configure_logging(with_rotating_file=True)

    # Set the log level for aiogram.event and httpx logger to CRITICAL
    aiogram_logger = logging.getLogger("aiogram.event")
    aiogram_logger.setLevel(logging.CRITICAL)
