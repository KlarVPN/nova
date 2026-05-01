from __future__ import annotations

from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from app.handlers.user.payment import yookassa_webhook_route
from app.services.crypto_pay_service import cryptopay_webhook_route
from app.services.freekassa_service import freekassa_webhook_route
from app.services.kassa_ai_service import kassa_ai_webhook_route
from app.services.panel_webhook_service import panel_webhook_route
from app.services.platega_service import platega_webhook_route
from app.services.severpay_service import severpay_webhook_route


class FastAPIRequestShim:
    def __init__(self, request: Request, app_payload: dict[str, Any]):
        self._request = request
        self.app = app_payload
        self.headers = request.headers

    async def json(self) -> Any:
        return await self._request.json()

    async def read(self) -> bytes:
        return await self._request.body()

    async def post(self) -> dict[str, Any]:
        form = await self._request.form()
        return dict(form)
def build_webhook_router(dp: Dispatcher, bot: Bot, settings) -> APIRouter:
    router = APIRouter(tags=["webhooks"])

    app_payload = {
        "bot": bot,
        "dp": dp,
        "settings": settings,
    }
    for key in (
        "yookassa_service",
        "lknpd_service",
        "subscription_service",
        "referral_service",
        "panel_service",
        "stars_service",
        "freekassa_service",
        "kassa_ai_service",
        "cryptopay_service",
        "panel_webhook_service",
        "platega_service",
        "severpay_service",
        "promo_code_service",
        "async_session_factory",
        "i18n_instance",
    ):
        if hasattr(dp, "workflow_data") and key in dp.workflow_data:  # type: ignore[attr-defined]
            app_payload[key] = dp.workflow_data[key]  # type: ignore[index]

    @router.post(settings.telegram_webhook_path)
    async def telegram_webhook(request: Request) -> dict[str, bool]:
        secret_expected = (settings.TELEGRAM_WEBHOOK_SECRET or "").strip()
        if secret_expected:
            secret_got = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if secret_got != secret_expected:
                raise HTTPException(status_code=401, detail="invalid secret")

        payload = await request.json()
        update = Update.model_validate(payload)
        await dp.feed_update(bot, update)
        return {"ok": True}

    @router.post(settings.cryptopay_webhook_path)
    async def cryptopay_webhook(request: Request) -> Response:
        shim = FastAPIRequestShim(request, app_payload)
        return await cryptopay_webhook_route(shim)

    @router.post(settings.freekassa_webhook_path)
    async def freekassa_webhook(request: Request) -> Response:
        shim = FastAPIRequestShim(request, app_payload)
        return await freekassa_webhook_route(shim)

    @router.post(settings.kassa_ai_webhook_path)
    async def kassa_ai_webhook(request: Request) -> Response:
        shim = FastAPIRequestShim(request, app_payload)
        return await kassa_ai_webhook_route(shim)

    @router.post(settings.platega_webhook_path)
    async def platega_webhook(request: Request) -> Response:
        shim = FastAPIRequestShim(request, app_payload)
        return await platega_webhook_route(shim)

    @router.post(settings.severpay_webhook_path)
    async def severpay_webhook(request: Request) -> Response:
        shim = FastAPIRequestShim(request, app_payload)
        return await severpay_webhook_route(shim)

    @router.post(settings.yookassa_webhook_path)
    async def yk_webhook(request: Request) -> Response:
        shim = FastAPIRequestShim(request, app_payload)
        return await yookassa_webhook_route(shim)

    @router.post(settings.panel_webhook_path)
    async def panel_webhook(request: Request) -> Response:
        shim = FastAPIRequestShim(request, app_payload)
        return await panel_webhook_route(shim)

    return router
