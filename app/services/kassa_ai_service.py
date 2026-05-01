import asyncio
from datetime import datetime
import hashlib
import hmac
import time
from typing import Any

from aiohttp import ClientSession, ClientTimeout
from fastapi.responses import PlainTextResponse, Response

from app.database.dal import payment_dal, user_dal
from app.keyboards.inline.user_keyboards import get_connect_and_main_keyboard
from app.logging_config import get_logger
from app.services.notification_service import NotificationService
from app.utils.config_link import prepare_config_links
from app.utils.text_sanitizer import sanitize_display_name, username_for_display

logger = get_logger(__name__)

IP_SERVICES = [
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
    "https://ipinfo.io/ip",
]


class KassaAiService:
    def __init__(
        self,
        *,
        bot,
        settings,
        i18n,
        async_session_factory,
        subscription_service,
        referral_service,
    ):
        self.bot = bot
        self.settings = settings
        self.i18n = i18n
        self.async_session_factory = async_session_factory
        self.subscription_service = subscription_service
        self.referral_service = referral_service

        self.api_base_url = "https://api.fk.life/v1"
        self._timeout = ClientTimeout(total=20)
        self._session: ClientSession | None = None
        self._nonce_lock = asyncio.Lock()
        self._last_nonce = int(time.time() * 1000)
        self._cached_public_ip: str | None = None

        self.shop_id = settings.KASSA_AI_SHOP_ID
        self.api_key = settings.KASSA_AI_API_KEY
        self.secret_word_2 = settings.KASSA_AI_SECRET_WORD_2
        self.default_currency = "RUB"
        self.payment_system_id = settings.KASSA_AI_PAYMENT_SYSTEM_ID or 44
        self.server_ip = settings.KASSA_AI_PAYMENT_IP

        self.configured = bool(settings.KASSA_AI_ENABLED and self.shop_id and self.api_key)
        if not self.configured:
            logger.warning("KassaAiService initialized but not fully configured")

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(timeout=self._timeout)
        return self._session

    async def _generate_nonce(self) -> int:
        async with self._nonce_lock:
            candidate = int(time.time() * 1000)
            if candidate <= self._last_nonce:
                candidate = self._last_nonce + 1
            self._last_nonce = candidate
            return candidate

    def _sign_payload(self, payload: dict[str, Any]) -> str:
        if not self.api_key:
            raise RuntimeError("Kassa AI API key is not configured")
        sign_data = {k: v for k, v in payload.items() if k != "signature" and v is not None}
        sorted_keys = sorted(sign_data.keys())
        message = "|".join(str(sign_data[k]) for k in sorted_keys)
        return hmac.new(self.api_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

    def _verify_webhook_signature(self, shop_id: str | int, amount_raw: str, order_id: str, sign: str) -> bool:
        if not self.secret_word_2:
            return False
        amount_clean = amount_raw.strip()
        if amount_clean.endswith(".00"):
            amount_clean = amount_clean[:-3]
        sign_str = f"{shop_id}:{amount_clean}:{self.secret_word_2}:{order_id}"
        expected = hashlib.md5(sign_str.encode("utf-8"), usedforsecurity=False).hexdigest()
        return hmac.compare_digest(expected.lower(), str(sign).lower())

    async def _resolve_public_ip(self) -> str:
        if self.server_ip:
            return self.server_ip
        if self._cached_public_ip:
            return self._cached_public_ip

        session = await self._get_session()
        for service_url in IP_SERVICES:
            try:
                async with session.get(service_url, timeout=ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        continue
                    ip = (await response.text()).strip()
                    if ip and len(ip.split(".")) == 4:
                        self._cached_public_ip = ip
                        return ip
            except Exception:
                continue

        self._cached_public_ip = "127.0.0.1"
        return self._cached_public_ip

    async def create_order(
        self,
        *,
        payment_db_id: int,
        user_id: int,
        months: int | float,
        amount: float,
        currency: str | None = None,
        email: str | None = None,
        payment_system_id: int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        if not self.configured:
            return False, {"message": "service_not_configured"}

        target_email = email or f"user_{user_id}@telegram.org"
        target_ip = await self._resolve_public_ip()
        ps_id = payment_system_id or self.payment_system_id
        amount_final: int | float = int(amount) if float(amount).is_integer() else amount

        payload: dict[str, Any] = {
            "shopId": int(self.shop_id),
            "nonce": await self._generate_nonce(),
            "paymentId": str(payment_db_id),
            "i": int(ps_id),
            "email": target_email,
            "ip": target_ip,
            "amount": amount_final,
            "currency": (currency or self.default_currency).upper(),
            "us_user_id": str(user_id),
            "us_months": str(months),
            "us_payment_db_id": str(payment_db_id),
        }
        payload["signature"] = self._sign_payload(payload)

        session = await self._get_session()
        try:
            async with session.post(f"{self.api_base_url}/orders/create", json=payload) as response:
                data = await response.json(content_type=None)
                if response.status != 200 or data.get("type") != "success":
                    logger.error("Kassa AI create_order failed", status=response.status, body=data)
                    return False, {"status": response.status, "message": data}
                return True, data
        except Exception as exc:
            logger.error("Kassa AI create_order request failed", error=str(exc), exc_info=True)
            return False, {"message": str(exc)}

    async def webhook_route(self, request) -> Response:
        if not self.configured:
            return PlainTextResponse("kassa_ai_disabled", status_code=503)

        try:
            data = await request.post()
            payload = {str(k): v for k, v in dict(data).items()}
        except Exception:
            try:
                json_payload = await request.json()
                payload = {str(k): v for k, v in json_payload.items()} if isinstance(json_payload, dict) else {}
            except Exception:
                payload = {}

        shop_id = payload.get("MERCHANT_ID") or payload.get("shopId")
        signature = payload.get("SIGN") or payload.get("sign") or payload.get("signature")
        order_id = payload.get("MERCHANT_ORDER_ID") or payload.get("order_id") or payload.get("paymentId")
        amount_raw = payload.get("AMOUNT") or payload.get("amount")
        provider_payment_id = payload.get("orderId") or payload.get("fk_order_id") or order_id

        if not shop_id or str(shop_id) != str(self.shop_id):
            return PlainTextResponse("merchant_mismatch", status_code=403)
        if not signature or not order_id or amount_raw is None:
            return PlainTextResponse("missing_data", status_code=400)
        if not self._verify_webhook_signature(shop_id, str(amount_raw), str(order_id), str(signature)):
            return PlainTextResponse("invalid_signature", status_code=403)

        try:
            payment_db_id = int(str(order_id))
        except Exception:
            return PlainTextResponse("invalid_order_id", status_code=400)

        async with self.async_session_factory() as session:
            payment = await payment_dal.get_payment_by_db_id(session, payment_db_id)
            if not payment:
                return PlainTextResponse("payment_not_found", status_code=404)

            if payment.status == "succeeded":
                return PlainTextResponse("YES")

            try:
                got = float(str(amount_raw).replace(",", "."))
                expected = float(payment.amount)
                if round(got, 2) != round(expected, 2):
                    return PlainTextResponse("amount_mismatch", status_code=400)
            except Exception:
                return PlainTextResponse("amount_validation_error", status_code=400)

            try:
                marked = await payment_dal.mark_provider_payment_succeeded_once(
                    session=session,
                    payment_db_id=payment.payment_id,
                    provider_payment_id=str(provider_payment_id or f"kassa_ai:{payment_db_id}"),
                )
                if not marked:
                    return PlainTextResponse("YES")

                sale_mode = "traffic" if self.settings.traffic_sale_mode else "subscription"
                units = payment.subscription_duration_months or 1

                activation = await self.subscription_service.activate_subscription(
                    session,
                    payment.user_id,
                    int(units) if sale_mode != "traffic" else 0,
                    float(payment.amount),
                    payment.payment_id,
                    promo_code_id_from_payment=payment.promo_code_id,
                    provider="kassa_ai",
                    sale_mode=sale_mode,
                    traffic_gb=units if sale_mode == "traffic" else None,
                )
                if not activation or not activation.get("end_date"):
                    raise RuntimeError("Kassa AI activation failed")

                referral_bonus = None
                if sale_mode != "traffic":
                    referral_bonus = await self.referral_service.apply_referral_bonuses_for_payment(
                        session,
                        payment.user_id,
                        int(units),
                        current_payment_db_id=payment.payment_id,
                        skip_if_active_before_payment=False,
                    )

                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.error("Kassa AI webhook processing failed", error=str(exc), exc_info=True)
                return PlainTextResponse("processing_error", status_code=500)

            db_user = payment.user or await user_dal.get_user_by_id(session, payment.user_id)
            lang = db_user.language_code if db_user and db_user.language_code else self.settings.DEFAULT_LANGUAGE
            _ = lambda k, **kw: self.i18n.gettext(lang, k, **kw) if self.i18n else k

            raw_config_link = activation.get("subscription_url") if activation else None
            config_link_display, connect_button_url = await prepare_config_links(self.settings, raw_config_link)
            config_link_text = config_link_display or _("config_link_not_available")
            final_end = activation.get("end_date")

            applied_days = 0
            if referral_bonus and referral_bonus.get("referee_new_end_date"):
                final_end = referral_bonus["referee_new_end_date"]
                applied_days = referral_bonus.get("referee_bonus_applied_days", 0)

            end_date_str = final_end.strftime("%Y-%m-%d") if final_end else _("config_link_not_available")

            if sale_mode == "traffic":
                traffic_label = str(int(units)) if float(units).is_integer() else f"{units:g}"
                text = _(
                    "payment_successful_traffic_full",
                    traffic_gb=traffic_label,
                    end_date=end_date_str if final_end else "",
                    config_link=config_link_text,
                )
            elif applied_days:
                inviter_name_display = _("friend_placeholder")
                if db_user and db_user.referred_by_id:
                    inviter = await user_dal.get_user_by_id(session, db_user.referred_by_id)
                    if inviter:
                        safe_name = sanitize_display_name(inviter.first_name) if inviter.first_name else None
                        if safe_name:
                            inviter_name_display = safe_name
                        elif inviter.username:
                            inviter_name_display = username_for_display(inviter.username, with_at=False)
                text = _(
                    "payment_successful_with_referral_bonus_full",
                    months=int(units),
                    base_end_date=activation["end_date"].strftime("%Y-%m-%d") if activation and activation.get("end_date") else end_date_str,
                    bonus_days=applied_days,
                    final_end_date=end_date_str,
                    inviter_name=inviter_name_display,
                    config_link=config_link_text,
                )
            else:
                text = _(
                    "payment_successful_full",
                    months=int(units),
                    end_date=end_date_str,
                    config_link=config_link_text,
                )

            order_info_text = _(
                "kassa_ai_order_full",
                order_id=str(provider_payment_id or payment_db_id),
                date=datetime.now().strftime("%Y-%m-%d"),
            )
            text = f"{order_info_text}\n{text}"

            markup = get_connect_and_main_keyboard(
                lang,
                self.i18n,
                self.settings,
                config_link_display,
                connect_button_url=connect_button_url,
                preserve_message=True,
            )
            try:
                await self.bot.send_message(
                    payment.user_id,
                    text,
                    reply_markup=markup,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
            except Exception as exc:
                logger.error("Kassa AI notification failed", user_id=payment.user_id, error=str(exc))

            try:
                notification_service = NotificationService(self.bot, self.settings, self.i18n)
                await notification_service.notify_payment_received(
                    user_id=payment.user_id,
                    amount=float(payment.amount),
                    currency=payment.currency,
                    months=int(units) if sale_mode != "traffic" else 0,
                    traffic_gb=units if sale_mode == "traffic" else None,
                    payment_provider="kassa_ai",
                    username=db_user.username if db_user else None,
                )
            except Exception as exc:
                logger.error("Kassa AI admin notification failed", error=str(exc))

        return PlainTextResponse("YES")

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


async def kassa_ai_webhook_route(request) -> Response:
    service: KassaAiService = request.app["kassa_ai_service"]
    return await service.webhook_route(request)
