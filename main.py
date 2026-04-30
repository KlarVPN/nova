import asyncio
import os
import signal
import sys

from dotenv import load_dotenv

from app.main_bot import run_bot
from app.support_bot.__main__ import run_support_bot
from app.config import get_settings
from app.database.database_setup import init_db, init_db_connection
from app.logging_config import configure_logging, get_logger

logger = get_logger(__name__)


async def main():
    load_dotenv()
    settings = get_settings()

    session_factory = init_db_connection(settings)
    if not session_factory:
        logger.critical("Failed to initialize DB connection and session factory. Exiting.")
        return

    await init_db(settings, session_factory)
    # Alembic reconfigures stdlib logging handlers during migrations.
    # Re-apply structlog pipeline so runtime logs keep structured formatting.
    configure_logging()

    tasks = [asyncio.create_task(run_bot(settings), name="main-vpn-bot")]

    support_bot_token = (os.getenv("SUPPORT_BOT_TOKEN") or "").strip()
    if support_bot_token:
        tasks.append(asyncio.create_task(run_support_bot(), name="support-bot"))
        logger.info("Support bot task enabled and started.")
    else:
        logger.info("SUPPORT_BOT_TOKEN is empty: support bot startup skipped.")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    stop_waiter = asyncio.create_task(stop_event.wait(), name="shutdown-signal-waiter")

    try:
        done, _ = await asyncio.wait(
            [*tasks, stop_waiter],
            return_when=asyncio.FIRST_COMPLETED,
        )
        if stop_waiter in done:
            logger.info("Shutdown signal received. Stopping bots...")
        for task in done:
            if task is stop_waiter or task.cancelled():
                continue
            exc = task.exception()
            if exc:
                raise exc
    finally:
        if not stop_waiter.done():
            stop_waiter.cancel()
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            done, pending = await asyncio.wait(tasks, timeout=10)
            for task in pending:
                logger.warning("Task did not stop in time", task_name=task.get_name())
            for task in done:
                if task.cancelled():
                    continue
                exc = task.exception()
                if exc:
                    logger.error("Task failed during shutdown", task_name=task.get_name(), error=str(exc))


if __name__ == "__main__":
    load_dotenv()
    configure_logging()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually")
    except Exception as e_global:
        logger.critical("Global unhandled exception in main", error=str(e_global), exc_info=True)
        sys.exit(1)
