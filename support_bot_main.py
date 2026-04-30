import asyncio

from src.support_bot.__main__ import main
from src.support_bot.logger import setup_logger


if __name__ == "__main__":
    setup_logger()
    asyncio.run(main())
