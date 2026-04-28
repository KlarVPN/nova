import asyncio
import logging
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from sqlalchemy.orm import sessionmaker

from src.config import Settings


async def build_and_start_web_app(
    dp: Dispatcher,
    bot: Bot,
    settings: Settings,
    async_session_factory: sessionmaker,
):
    app = web.Application()
    app["bot"] = bot
    app["dp"] = dp
    app["settings"] = settings
    app["async_session_factory"] = async_session_factory

    # Cache bot username for referral link generation
    try:
        bot_info = await bot.get_me()
        app["bot_username"] = bot_info.username or ""
    except Exception:
        app["bot_username"] = ""
    # Inject shared instances used by webhook handlers
    app["i18n"] = dp.get("i18n_instance")
    for key in (
        "yookassa_service",
        "lknpd_service",
        "subscription_service",
        "referral_service",
        "panel_service",
        "stars_service",
        "freekassa_service",
        "cryptopay_service",
        "panel_webhook_service",
        "platega_service",
        "severpay_service",
        "promo_code_service",
    ):
        # Access dispatcher workflow_data directly to avoid sequence protocol issues
        if hasattr(dp, "workflow_data") and key in dp.workflow_data:  # type: ignore
            app[key] = dp.workflow_data[key]  # type: ignore

    setup_application(app, dp, bot=bot)

    telegram_uses_webhook_mode = bool(settings.WEBHOOK_BASE_URL)
    telegram_webhook_secret = (settings.TELEGRAM_WEBHOOK_SECRET or "").strip() or None

    if telegram_uses_webhook_mode:
        telegram_webhook_path = settings.telegram_webhook_path
        app.router.add_post(
            telegram_webhook_path,
            SimpleRequestHandler(
                dispatcher=dp,
                bot=bot,
                secret_token=telegram_webhook_secret,
            ),
        )
        logging.info(
            "Telegram webhook route configured at: [POST] %s (secret_token=%s)",
            telegram_webhook_path,
            "set" if telegram_webhook_secret else "not_set",
        )

    from src.handlers.user.payment import yookassa_webhook_route
    from src.services.crypto_pay_service import cryptopay_webhook_route
    from src.services.panel_webhook_service import panel_webhook_route
    from src.services.freekassa_service import freekassa_webhook_route
    from src.services.platega_service import platega_webhook_route
    from src.services.severpay_service import severpay_webhook_route

    cp_path = settings.cryptopay_webhook_path
    if cp_path.startswith("/"):
        app.router.add_post(cp_path, cryptopay_webhook_route)
        logging.info("CryptoPay webhook route configured at: [POST] %s", cp_path)

    fk_path = settings.freekassa_webhook_path
    if fk_path.startswith("/"):
        app.router.add_post(fk_path, freekassa_webhook_route)
        logging.info(f"FreeKassa webhook route configured at: [POST] {fk_path}")

    pg_path = settings.platega_webhook_path
    if pg_path.startswith("/"):
        app.router.add_post(pg_path, platega_webhook_route)
        logging.info(f"Platega webhook route configured at: [POST] {pg_path}")

    sp_path = settings.severpay_webhook_path
    if sp_path.startswith("/"):
        app.router.add_post(sp_path, severpay_webhook_route)
        logging.info(f"SeverPay webhook route configured at: [POST] {sp_path}")

    # YooKassa webhook (register only when base URL present and path configured)
    yk_path = settings.yookassa_webhook_path
    if settings.WEBHOOK_BASE_URL and yk_path and yk_path.startswith("/"):
        app.router.add_post(yk_path, yookassa_webhook_route)
        logging.info(f"YooKassa webhook route configured at: [POST] {yk_path}")

    panel_path = settings.panel_webhook_path
    if panel_path.startswith("/"):
        app.router.add_post(panel_path, panel_webhook_route)
        logging.info(f"Panel webhook route configured at: [POST] {panel_path}")

    # Mini App API routes
    from src.app.web.api.routes import router as api_router
    app.router.add_routes(api_router)
    logging.info("Mini App API routes registered at /api/*")

    # Serve Mini App static files if dist exists
    miniapp_dist = Path(__file__).parent.parent.parent.parent / "webapp" / "dist"
    if miniapp_dist.exists():
        app.router.add_static("/app", miniapp_dist, name="miniapp_static", show_index=True)

        async def miniapp_index(_: web.Request) -> web.FileResponse:
            return web.FileResponse(miniapp_dist / "index.html")

        app.router.add_get("/app", miniapp_index)
        logging.info("Mini App static files served from %s", miniapp_dist)

    web_app_runner = web.AppRunner(app)
    await web_app_runner.setup()
    site = web.TCPSite(
        web_app_runner,
        host=settings.WEB_SERVER_HOST,
        port=settings.WEB_SERVER_PORT,
    )

    await site.start()
    logging.info(
        f"AIOHTTP server started on http://{settings.WEB_SERVER_HOST}:{settings.WEB_SERVER_PORT}"
    )

    # Run until cancelled
    await asyncio.Event().wait()
