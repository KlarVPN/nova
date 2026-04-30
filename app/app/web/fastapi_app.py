from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.app.web.fastapi_api import router as api_router
from app.app.web.fastapi_webhooks import build_webhook_router


def create_fastapi_app(
    *,
    settings=None,
    async_session_factory=None,
    panel_service=None,
    subscription_service=None,
    promo_code_service=None,
    yookassa_service=None,
    cryptopay_service=None,
    freekassa_service=None,
    platega_service=None,
    severpay_service=None,
    bot_username: str = "",
    dp=None,
    bot=None,
) -> FastAPI:
    app = FastAPI(title="KLAR API", version="1.0.0")

    app.state.settings = settings
    app.state.async_session_factory = async_session_factory
    app.state.panel_service = panel_service
    app.state.subscription_service = subscription_service
    app.state.promo_code_service = promo_code_service
    app.state.yookassa_service = yookassa_service
    app.state.cryptopay_service = cryptopay_service
    app.state.freekassa_service = freekassa_service
    app.state.platega_service = platega_service
    app.state.severpay_service = severpay_service
    app.state.bot_username = bot_username
    app.state.dp = dp
    app.state.bot = bot

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    app.include_router(api_router)

    if settings is not None and dp is not None and bot is not None:
        app.include_router(build_webhook_router(dp, bot, settings))

    @app.get("/th/{access_uuid}")
    async def access_link_redirect(access_uuid: str) -> RedirectResponse:
        return RedirectResponse(url=f"/app/th/{access_uuid}", status_code=307)

    cabinet_dist = Path(__file__).resolve().parents[3] / "cabinet" / "dist"
    if cabinet_dist.exists():
        app.mount("/app/assets", StaticFiles(directory=str(cabinet_dist / "assets")), name="cabinet_assets")

        @app.get("/app", include_in_schema=False)
        @app.get("/app/{path:path}", include_in_schema=False)
        async def serve_spa(path: str = "") -> FileResponse:
            file_path = cabinet_dist / path
            if path and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(cabinet_dist / "index.html"))

    return app
