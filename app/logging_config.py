import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

import structlog


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


def _configure_structlog(level: int, use_colors: bool) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer = structlog.dev.ConsoleRenderer(colors=use_colors)
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    logging.captureWarnings(True)

    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        framework_logger = logging.getLogger(logger_name)
        framework_logger.handlers.clear()
        framework_logger.propagate = True
        framework_logger.setLevel(level)


def configure_logging(with_rotating_file: bool = False) -> None:
    level = resolve_log_level(os.getenv("LOG_LEVEL", "INFO"))
    _configure_structlog(level=level, use_colors=True)

    if with_rotating_file:
        try:
            os.makedirs(".logs", exist_ok=True)
            file_handler = TimedRotatingFileHandler(
                filename=f".logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log",
                when="midnight",
                interval=1,
                backupCount=7,
            )
            file_formatter = structlog.stdlib.ProcessorFormatter(
                foreign_pre_chain=[
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                ],
                processors=[
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.JSONRenderer(),
                ],
            )
            file_handler.setFormatter(file_formatter)
            logging.getLogger().addHandler(file_handler)
        except OSError:
            pass


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger()
