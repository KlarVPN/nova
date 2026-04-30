import asyncio

from app.support_bot.__main__ import main
from app.support_bot.logger import setup_logger


if __name__ == "__main__":
    setup_logger()
    asyncio.run(main())
