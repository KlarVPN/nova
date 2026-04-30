import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from src.logging_config import ColorFormatter, build_default_formatter, resolve_log_level


def setup_logger() -> None:
    """
    Set up the logger configuration for the application.

    This function ensures that the logs directory exists, configures basic logging,
    and sets the log level for specific loggers.

    Logs are written to both a timed rotating file handler and a stream handler.

    - Logs are saved to files in the ".logs" directory with a one-day rotation.
    - The console (stream) handler displays logs on the console.

    The log level for the "aiogram.event" and "httpx" loggers is set to CRITICAL.

    :return: None
    """
    root = logging.getLogger()
    root.setLevel(resolve_log_level(os.getenv("LOG_LEVEL", "INFO")))
    root.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter("%(levelname).5s [%(name)s] %(message)s"))
    handlers = [console_handler]

    # Ensure the logs directory exists
    try:
        os.makedirs(".logs", exist_ok=True)
        handlers.insert(
            0,
            TimedRotatingFileHandler(
                filename=f".logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log",
                when="midnight",
                interval=1,
                backupCount=7,
            ),
        )
        handlers[0].setFormatter(build_default_formatter())
    except OSError:
        pass

    for handler in handlers:
        root.addHandler(handler)

    # Set the log level for aiogram.event and httpx logger to CRITICAL
    aiogram_logger = logging.getLogger("aiogram.event")
    aiogram_logger.setLevel(logging.CRITICAL)
