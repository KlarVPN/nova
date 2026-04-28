import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import web

from .auth import validate_init_data
from src.database.dal import user_dal, subscription_dal
from src.database.dal.active_discount_dal import get_active_discount

log = logging.getLogger(__name__)

router = web.RouteTableDef()


def _json(data: Any, status: int = 200) -> web.Response:
    return web.Response(
        body=json.dumps(data, ensure_ascii=False, default=str),
        content_type="application/json",
        status=status,
    )


def _error(detail: str, status: int = 400) -> web.Response:
    return _json({"detail": detail}, status=status)


async def _get_user(request: web.Request) -> tuple[dict | None, web.Response | None]:
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    settings = request.app["settings"]

    tg_user = validate_init_data(init_data, settings.BOT_TOKEN)
    if not tg_user:
        return None, _error("Unauthorized", 401)
    return tg_user, None


def _sub_to_dict(sub) -> dict:
    now = datetime.now(timezone.utc)
    end = sub.end_date
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    days_remaining = max(0, (end - now).days) if end else 0

    traffic_limit_gb = None
    traffic_used_gb = None
    traffic_remaining_pct = None

    if sub.traffic_limit_bytes:
        traffic_limit_gb = round(sub.traffic_limit_bytes / (1024**3), 2)
        used = sub.traffic_used_bytes or 0
        traffic_used_gb = round(used / (1024**3), 2)
        traffic_remaining_pct = round(
            max(0, (sub.traffic_limit_bytes - used) / sub.traffic_limit_bytes * 100), 1
        )

    return {
        "subscription_id": sub.subscription_id,
        "start_date": sub.start_date.isoformat() if sub.start_date else None,
        "end_date": end.isoformat() if end else None,
        "duration_months": sub.duration_months,
        "is_active": sub.is_active,
        "auto_renew_enabled": sub.auto_renew_enabled,
        "days_remaining": days_remaining,
        "traffic_limit_gb": traffic_limit_gb,
        "traffic_used_gb": traffic_used_gb,
        "traffic_remaining_pct": traffic_remaining_pct,
        "provider": sub.provider or "",
        "status_from_panel": sub.status_from_panel or "ACTIVE",
    }


# ─── User ────────────────────────────────────────────────────────────────────

@router.get("/api/user/me")
async def get_me(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]
    session_factory = request.app["async_session_factory"]

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if not user:
            return _error("User not found", 404)

        sub = await subscription_dal.get_active_subscription_by_user_id(session, user_id)
        has_any = await subscription_dal.has_any_subscription_for_user(session, user_id)
        settings = request.app["settings"]

        trial_available = (
            settings.TRIAL_ENABLED
            and not has_any
            and not user.is_banned
        )

        return _json({
            "user_id": user.user_id,
            "first_name": user.first_name or tg_user.get("first_name", ""),
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code or "ru",
            "referral_code": user.referral_code or "",
            "is_banned": user.is_banned,
            "has_active_subscription": sub is not None and sub.is_active,
            "subscription": _sub_to_dict(sub) if sub else None,
            "trial_available": trial_available,
        })


# ─── Plans ────────────────────────────────────────────────────────────────────

@router.get("/api/plans")
async def get_plans(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]
    settings = request.app["settings"]
    session_factory = request.app["async_session_factory"]

    async with session_factory() as session:
        discount_row = await get_active_discount(session, user_id)
        has_any = await subscription_dal.has_any_subscription_for_user(session, user_id)

    plans = []
    month_configs = [
        (1, settings.MONTH_1_ENABLED, settings.RUB_PRICE_1_MONTHS, settings.STARS_PRICE_1_MONTHS),
        (3, settings.MONTH_3_ENABLED, settings.RUB_PRICE_3_MONTHS, settings.STARS_PRICE_3_MONTHS),
        (6, settings.MONTH_6_ENABLED, settings.RUB_PRICE_6_MONTHS, settings.STARS_PRICE_6_MONTHS),
        (12, settings.MONTH_12_ENABLED, settings.RUB_PRICE_12_MONTHS, settings.STARS_PRICE_12_MONTHS),
    ]
    for months, enabled, rub_price, stars_price in month_configs:
        plans.append({
            "months": months,
            "price_rub": rub_price,
            "price_stars": stars_price,
            "enabled": enabled and rub_price is not None,
            "is_popular": months == 6,
            "is_best_value": months == 12,
        })

    traffic_packages = [
        {"gb": gb, "price_rub": price, "price_stars": None}
        for gb, price in settings.traffic_packages.items()
    ]

    active_discount = None
    if discount_row:
        expires = discount_row.expires_at
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        active_discount = {
            "discount_percentage": discount_row.discount_percentage,
            "promo_code": "",
            "expires_at": expires.isoformat() if expires else None,
        }

    methods_order = settings.payment_methods_order
    active_methods = []
    if settings.YOOKASSA_ENABLED and "yookassa" in methods_order:
        active_methods.append("yookassa")
    if settings.STARS_ENABLED and "stars" in methods_order:
        active_methods.append("stars")
    if settings.CRYPTOPAY_ENABLED and "cryptopay" in methods_order:
        active_methods.append("cryptopay")
    if settings.FREEKASSA_ENABLED and "freekassa" in methods_order:
        active_methods.append("freekassa")
    if settings.PLATEGA_ENABLED and "platega" in methods_order:
        active_methods.append("platega")
    if settings.SEVERPAY_ENABLED and "severpay" in methods_order:
        active_methods.append("severpay")

    return _json({
        "traffic_sale_mode": settings.traffic_sale_mode,
        "plans": plans,
        "traffic_packages": traffic_packages,
        "active_discount": active_discount,
        "payment_methods": active_methods,
        "trial_enabled": settings.TRIAL_ENABLED,
        "trial_days": settings.TRIAL_DURATION_DAYS,
        "trial_traffic_gb": settings.TRIAL_TRAFFIC_LIMIT_GB,
        "has_had_subscription": has_any,
    })


# ─── Referral ─────────────────────────────────────────────────────────────────

@router.get("/api/referral")
async def get_referral(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]
    settings = request.app["settings"]
    session_factory = request.app["async_session_factory"]

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if not user:
            return _error("User not found", 404)

        referral_code = await user_dal.ensure_referral_code(session, user)
        await session.commit()

        from sqlalchemy import select, func
        from src.database.models import User
        referred_count_result = await session.execute(
            select(func.count()).where(User.referred_by_id == user_id)
        )
        referred_count = referred_count_result.scalar() or 0

        from src.database.models import Payment
        purchased_result = await session.execute(
            select(func.count(Payment.payment_id.distinct()))
            .join(User, User.user_id == Payment.user_id)
            .where(User.referred_by_id == user_id, Payment.status == "succeeded")
        )
        purchased_count = purchased_result.scalar() or 0

    bot_username = request.app.get("bot_username", "")
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}" if bot_username else ""

    bonus_structure = {}
    for months in [1, 3, 6, 12]:
        inviter_days = settings.referral_bonus_inviter.get(months, 0)
        referee_days = settings.referral_bonus_referee.get(months, 0)
        bonus_structure[str(months)] = {
            "inviter_days": inviter_days,
            "referee_days": referee_days,
        }

    return _json({
        "referral_code": referral_code,
        "referral_link": referral_link,
        "referred_count": referred_count,
        "purchased_count": purchased_count,
        "bonus_structure": bonus_structure,
    })


# ─── Promo ────────────────────────────────────────────────────────────────────

@router.post("/api/promo/apply")
async def apply_promo(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]

    try:
        body = await request.json()
        code: str = body.get("code", "").strip().upper()
    except Exception:
        return _error("Invalid request body")

    if not code:
        return _error("Code is required")

    session_factory = request.app["async_session_factory"]
    promo_service = request.app.get("promo_code_service")

    if not promo_service:
        return _error("Service unavailable", 503)

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if not user:
            return _error("User not found", 404)

        lang = user.language_code or "ru"
        success, result = await promo_service.apply_promo_code(session, user_id, code, lang)

        if success:
            from datetime import timezone
            new_end = result
            if isinstance(new_end, datetime):
                if new_end.tzinfo is None:
                    new_end = new_end.replace(tzinfo=timezone.utc)
                await session.commit()
                return _json({
                    "success": True,
                    "type": "bonus_days",
                    "new_end_date": new_end.isoformat(),
                })

        # Try discount type
        ok2, res2 = await promo_service.apply_discount_promo_code(session, user_id, code, lang)
        if ok2:
            discount_pct = res2
            discount_row = await get_active_discount(session, user_id)
            expires = None
            if discount_row and discount_row.expires_at:
                expires = discount_row.expires_at
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
            await session.commit()
            return _json({
                "success": True,
                "type": "discount",
                "discount_percentage": discount_pct,
                "expires_at": expires.isoformat() if expires else None,
            })

        await session.rollback()
        error_reason = result if isinstance(result, str) else "not_found"
        return _json({"success": False, "error": error_reason})


# ─── Subscription Connect ─────────────────────────────────────────────────────

@router.get("/api/subscription/connect")
async def get_connect(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]
    session_factory = request.app["async_session_factory"]
    sub_service = request.app.get("subscription_service")

    if not sub_service:
        return _error("Service unavailable", 503)

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if not user or not user.panel_user_uuid:
            return _error("No active subscription", 404)

        sub = await subscription_dal.get_active_subscription_by_user_id(session, user_id)
        if not sub:
            return _error("No active subscription", 404)

    panel_service = request.app.get("panel_service")
    if not panel_service:
        return _error("Service unavailable", 503)

    try:
        panel_user = await panel_service.get_user_by_uuid(user.panel_user_uuid)
        sub_url = panel_user.get("subscriptionUrl", "")
        return _json({
            "connect_url": sub_url,
            "config_link": sub_url,
        })
    except Exception as e:
        log.warning("Failed to get connect info for user %s: %s", user_id, e)
        return _error("Failed to retrieve connection info", 502)


# ─── Payment Create ───────────────────────────────────────────────────────────

@router.post("/api/payment/create")
async def create_payment(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]

    try:
        body = await request.json()
        months: int | None = body.get("months")
        gb: float | None = body.get("gb")
        provider: str = body.get("provider", "")
    except Exception:
        return _error("Invalid request body")

    if not provider:
        return _error("Provider is required")
    if not months and not gb:
        return _error("months or gb is required")

    settings = request.app["settings"]
    session_factory = request.app["async_session_factory"]

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if not user:
            return _error("User not found", 404)

        discount = await get_active_discount(session, user_id)
        discount_pct = discount.discount_percentage if discount else 0

    # Calculate price
    if months:
        base_price = settings.subscription_options.get(months)
        stars_price = settings.stars_subscription_options.get(months)
    else:
        base_price = settings.traffic_packages.get(gb)
        stars_price = settings.stars_traffic_packages.get(gb)

    if base_price is None and provider != "stars":
        return _error("Invalid plan selected")

    if provider == "stars":
        price = stars_price
    else:
        price = base_price
        if discount_pct and price:
            price = int(price * (1 - discount_pct / 100))

    # Build description
    if months:
        from src.lib.utils import monthsLabel  # noqa – not available, use inline
        desc = f"Nova VPN — {months} мес."
    else:
        desc = f"Nova VPN — {gb} GB"

    # Create payment via provider service
    metadata = {
        "user_id": user_id,
        "subscription_months": months,
        "traffic_gb": gb,
    }

    try:
        if provider == "yookassa":
            svc = request.app.get("yookassa_service")
            if not svc:
                return _error("Yookassa not configured", 503)
            payment = await svc.create_payment(
                amount=str(price),
                currency="RUB",
                description=desc,
                metadata=metadata,
            )
            return _json({
                "payment_id": payment.get("id", ""),
                "payment_url": payment.get("confirmation", {}).get("confirmation_url"),
                "invoice_link": None,
                "provider": provider,
            })

        elif provider == "stars":
            bot = request.app["bot"]
            invoice = await bot.create_invoice_link(
                title="Nova VPN",
                description=desc,
                payload=f"miniapp_{user_id}_{months or gb}",
                currency="XTR",
                prices=[{"label": "Nova VPN", "amount": int(stars_price or 1)}],
            )
            return _json({
                "payment_id": "",
                "payment_url": None,
                "invoice_link": invoice,
                "provider": provider,
            })

        elif provider == "cryptopay":
            svc = request.app.get("cryptopay_service")
            if not svc:
                return _error("CryptoPay not configured", 503)
            invoice = await svc.create_invoice(
                amount=str(price),
                currency="RUB",
                description=desc,
                metadata=metadata,
            )
            return _json({
                "payment_id": str(invoice.get("invoice_id", "")),
                "payment_url": invoice.get("pay_url"),
                "invoice_link": None,
                "provider": provider,
            })

        else:
            return _error(f"Provider '{provider}' not supported via Mini App", 400)

    except Exception as e:
        log.error("Payment creation failed for user %s provider %s: %s", user_id, provider, e)
        return _error("Payment creation failed", 502)


# ─── Devices ──────────────────────────────────────────────────────────────────

@router.get("/api/devices")
async def get_devices(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]
    session_factory = request.app["async_session_factory"]
    panel_service = request.app.get("panel_service")

    if not panel_service:
        return _error("Service unavailable", 503)

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if not user or not user.panel_user_uuid:
            return _error("No active subscription", 404)
        sub = await subscription_dal.get_active_subscription_by_user_id(session, user_id)
        if not sub:
            return _error("No active subscription", 404)

    try:
        devices_response, panel_user = await asyncio.gather(
            panel_service.get_user_devices(user.panel_user_uuid),
            panel_service.get_user_by_uuid(user.panel_user_uuid),
        )

        devices_list = []
        if isinstance(devices_response, dict):
            devices_list = devices_response.get("devices") or []
        elif isinstance(devices_response, list):
            devices_list = devices_response

        max_devices = None
        if panel_user:
            limit = panel_user.get("hwidDeviceLimit")
            if limit is not None and int(limit) > 0:
                max_devices = int(limit)

        return _json({
            "devices": devices_list,
            "current_count": len(devices_list),
            "max_devices": max_devices,
        })
    except Exception as e:
        log.warning("Failed to get devices for user %s: %s", user_id, e)
        return _error("Failed to retrieve devices", 502)


@router.post("/api/devices/disconnect")
async def disconnect_device_endpoint(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]

    try:
        body = await request.json()
        hwid: str = body.get("hwid", "").strip()
    except Exception:
        return _error("Invalid request body")

    if not hwid:
        return _error("hwid is required")

    session_factory = request.app["async_session_factory"]
    panel_service = request.app.get("panel_service")

    if not panel_service:
        return _error("Service unavailable", 503)

    async with session_factory() as session:
        user = await user_dal.get_user_by_id(session, user_id)
        if not user or not user.panel_user_uuid:
            return _error("No active subscription", 404)

    try:
        success = await panel_service.disconnect_device(user.panel_user_uuid, hwid)
        if success:
            return _json({"success": True})
        return _error("Failed to disconnect device", 502)
    except Exception as e:
        log.warning("Failed to disconnect device for user %s: %s", user_id, e)
        return _error("Failed to disconnect device", 502)


# ─── Trial Activation ─────────────────────────────────────────────────────────

@router.post("/api/payment/trial")
async def activate_trial(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    user_id: int = tg_user["id"]
    settings = request.app["settings"]

    if not settings.TRIAL_ENABLED:
        return _error("Trial is not enabled", 403)

    session_factory = request.app["async_session_factory"]
    sub_service = request.app.get("subscription_service")

    if not sub_service:
        return _error("Service unavailable", 503)

    try:
        async with session_factory() as session:
            has_any = await subscription_dal.has_any_subscription_for_user(session, user_id)
            if has_any:
                return _error("Trial already used", 403)

            user = await user_dal.get_user_by_id(session, user_id)
            if not user:
                return _error("User not found", 404)

            result = await sub_service.activate_trial_subscription(session, user_id)
            if not result:
                return _error("Trial activation failed", 502)
            if not result.get("eligible"):
                return _error("Trial already used", 403)
            if not result.get("activated"):
                return _error("Trial activation failed", 502)

            end_date = result.get("end_date")
            return _json(
                {
                    "success": True,
                    "end_date": end_date.isoformat() if end_date else None,
                }
            )
    except Exception as e:
        log.error("Trial activation failed for user %s: %s", user_id, e, exc_info=True)
        return _error("Trial activation failed", 502)
