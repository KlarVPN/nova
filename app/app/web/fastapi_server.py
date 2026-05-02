import logging
import asyncio

import uvicorn
from aiogram import Bot, Dispatcher
from sqlalchemy.orm import sessionmaker

from app.app.web.fastapi_app import create_fastapi_app
from app.config import Settings


async def build_and_start_fastapi_app(
    dp: Dispatcher,
    bot: Bot,
    settings: Settings,
    async_session_factory: sessionmaker,
):
    bot_username = ""
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username or ""
    except Exception:
        bot_username = ""

    app = create_fastapi_app(
        settings=settings,
        async_session_factory=async_session_factory,
        panel_service=dp.get("panel_service"),
        subscription_service=dp.get("subscription_service"),
        promo_code_service=dp.get("promo_code_service"),
        yookassa_service=dp.get("yookassa_service"),
        cryptopay_service=dp.get("cryptopay_service"),
        freekassa_service=dp.get("freekassa_service"),
        platega_service=dp.get("platega_service"),
        severpay_service=dp.get("severpay_service"),
        kassa_ai_service=dp.get("kassa_ai_service"),
        bot_username=bot_username,
        dp=dp,
        bot=bot,
        i18n_instance=dp.get("i18n_instance"),
    )

    config = uvicorn.Config(
        app=app,
        host=settings.WEB_SERVER_HOST,
        port=settings.WEB_SERVER_PORT,
        log_level="info",
        loop="asyncio",
        log_config=None,
    )
    server = uvicorn.Server(config)

    logging.info(
        "FastAPI server starting on http://%s:%s",
        settings.WEB_SERVER_HOST,
        settings.WEB_SERVER_PORT,
    )

    try:
        await server.serve()
    except asyncio.CancelledError:
        logging.info("FastAPI server task cancelled during shutdown")
