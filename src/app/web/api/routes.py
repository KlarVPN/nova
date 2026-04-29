import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import ClientSession, ClientTimeout, web

from .auth import validate_init_data
from src.database.dal import user_dal, subscription_dal, payment_dal
from src.database.dal.active_discount_dal import get_active_discount
from src.cache.redis_client import get_redis_client

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


async def _fetch_kuma_monitors(status_url: str) -> list[dict[str, Any]]:
    timeout = ClientTimeout(total=10)
    async with ClientSession(timeout=timeout) as client:
        async with client.get(status_url) as resp:
            if resp.status != 200:
                return []
            data = await resp.json(content_type=None)

    if isinstance(data, dict):
        if isinstance(data.get("monitors"), list):
            return data["monitors"]
        if isinstance(data.get("data"), dict) and isinstance(data["data"].get("monitors"), list):
            return data["data"]["monitors"]
        if isinstance(data.get("monitorList"), list):
            return data["monitorList"]
    if isinstance(data, list):
        return data
    return []


async def _fetch_json(url: str) -> dict[str, Any] | list[Any] | None:
    timeout = ClientTimeout(total=15)
    async with ClientSession(timeout=timeout) as client:
        async with client.get(url) as resp:
            if resp.status != 200:
                return None
            return await resp.json(content_type=None)


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
            "links": {
                "support": settings.SUPPORT_LINK or "",
                "docs": settings.DOCS_URL or "",
                "reviews": settings.REVIEWS_URL or "",
                "terms": settings.TERMS_OF_SERVICE_URL or "",
                "privacy": settings.PRIVACY_POLICY_URL or "",
                "instruction_ios": settings.INSTRUCTION_IOS_URL or "",
                "instruction_android": settings.INSTRUCTION_ANDROID_URL or "",
                "instruction_macos": settings.INSTRUCTION_MACOS_URL or "",
                "instruction_windows": settings.INSTRUCTION_WINDOWS_URL or "",
                "instruction_linux": settings.INSTRUCTION_LINUX_URL or "",
            },
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
        (1, settings.MONTH_1_ENABLED, settings.RUB_PRICE_1_MONTH, settings.STARS_PRICE_1_MONTH),
        (3, settings.MONTH_3_ENABLED, settings.RUB_PRICE_3_MONTHS, settings.STARS_PRICE_3_MONTHS),
        (6, settings.MONTH_6_ENABLED, settings.RUB_PRICE_6_MONTHS, settings.STARS_PRICE_6_MONTHS),
        (12, settings.MONTH_12_ENABLED, settings.RUB_PRICE_12_MONTHS, settings.STARS_PRICE_12_MONTHS),
    ]
    for months, enabled, rub_price, stars_price in month_configs:
        has_price = rub_price is not None or stars_price is not None
        plans.append({
            "months": months,
            "price_rub": rub_price,
            "price_stars": stars_price,
            "enabled": bool(enabled and has_price),
            "is_popular": months == 6,
            "is_best_value": months == 12,
        })

    traffic_packages_map: dict[float, dict[str, float | None]] = {}
    for gb, rub_price in settings.traffic_packages.items():
        traffic_packages_map[float(gb)] = {"price_rub": rub_price, "price_stars": None}
    for gb, stars_price in settings.stars_traffic_packages.items():
        key = float(gb)
        pkg = traffic_packages_map.get(key)
        if pkg is None:
            traffic_packages_map[key] = {"price_rub": None, "price_stars": stars_price}
        else:
            pkg["price_stars"] = stars_price

    traffic_packages = [
        {"gb": gb, "price_rub": data["price_rub"], "price_stars": data["price_stars"]}
        for gb, data in sorted(traffic_packages_map.items(), key=lambda item: item[0])
        if data["price_rub"] is not None or data["price_stars"] is not None
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
        "included_traffic_gb": settings.USER_TRAFFIC_LIMIT_GB,
        "max_devices": settings.USER_HWID_DEVICE_LIMIT,
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


# ─── Locations ────────────────────────────────────────────────────────────────

@router.get("/api/proxies")
async def get_proxies(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    _ = tg_user
    settings = request.app["settings"]

    proxies = [
        {
            "country": proxy.country,
            "emoji": proxy.emoji,
            "link": proxy.link,
        }
        for proxy in (settings.PROXIES or [])
        if proxy.link
    ]

    return _json({"proxies": proxies})


# ─── Locations ────────────────────────────────────────────────────────────────

@router.get("/api/locations")
async def get_locations(request: web.Request) -> web.Response:
    tg_user, err = await _get_user(request)
    if err:
        return err

    _ = tg_user
    settings = request.app["settings"]
    status_url = (settings.UPTIME_KUMA_STATUS_URL or "").strip()
    if not status_url:
        return _json({"locations": []})

    redis_client = get_redis_client()
    cache_key = f"miniapp:locations:{status_url}"
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return web.Response(
                    body=cached,
                    content_type="application/json",
                    status=200,
                )
        except Exception as e:
            log.warning("Locations cache read failed: %r", e)

    if status_url:
        try:
            status_data = await _fetch_json(status_url)
        except Exception as e:
            log.warning(
                "Failed to fetch Uptime Kuma status from %s: %r",
                status_url,
                e,
            )
            return _json({"locations": []})

    if not isinstance(status_data, dict):
        return _json({"locations": []})

    # Main status page payload contains publicGroupList[*].monitorList[*]
    monitors: list[dict[str, Any]] = []
    for group in status_data.get("publicGroupList", []) or []:
        group_name = str(group.get("name") or "")
        for mon in group.get("monitorList", []) or []:
            if isinstance(mon, dict):
                mon = {**mon, "_group": group_name}
                monitors.append(mon)

    # Fallback if custom schema uses top-level monitors key
    if not monitors and isinstance(status_data.get("monitors"), list):
        monitors = [m for m in status_data.get("monitors", []) if isinstance(m, dict)]

    heartbeat_url = status_url.replace("/api/status-page/", "/api/status-page/heartbeat/")
    heartbeat_data: dict[str, Any] | list[Any] | None = None
    try:
        heartbeat_data = await _fetch_json(heartbeat_url)
    except Exception as e:
        log.warning(
            "Failed to fetch Uptime Kuma heartbeat from %s: %r",
            heartbeat_url,
            e,
        )

    heartbeat_map: dict[str, list[dict[str, Any]]] = {}
    if isinstance(heartbeat_data, dict) and isinstance(heartbeat_data.get("heartbeatList"), dict):
        for key, value in heartbeat_data["heartbeatList"].items():
            if isinstance(value, list):
                heartbeat_map[str(key)] = [item for item in value if isinstance(item, dict)]

    items: list[dict[str, Any]] = []
    for mon in monitors:
        monitor_id = mon.get("id")
        monitor_name = str(mon.get("name") or "")
        country = str(mon.get("_group") or "")

        latest_hb = None
        hb_list = heartbeat_map.get(str(monitor_id), [])
        if hb_list:
            latest_hb = hb_list[-1]

        status = "unknown"
        status_val = None
        if latest_hb is not None:
            status_val = latest_hb.get("status")
        elif "status" in mon:
            status_val = mon.get("status")

        if status_val in (1, "1", "up", "UP", "online", "ONLINE", "ok", "OK"):
            status = "online"
        elif status_val in (0, "0", "down", "DOWN", "offline", "OFFLINE"):
            status = "offline"
        elif status_val in (2, "2", "pending", "PENDING"):
            status = "pending"

        ping_raw = None
        if latest_hb is not None:
            ping_raw = latest_hb.get("ping")
        if ping_raw is None:
            ping_raw = mon.get("ping")

        ping_ms: float | None = None
        if ping_raw is not None:
            try:
                ping_ms = float(ping_raw)
            except (TypeError, ValueError):
                ping_ms = None

        items.append(
            {
                "name": monitor_name,
                "country": country,
                "emoji": "",
                "status": status,
                "ping_ms": ping_ms,
                "uptime_pct": round(
                    (
                        sum(1 for hb in hb_list if hb.get("status") in (1, "1"))
                        / len(hb_list)
                        * 100
                    ),
                    1,
                )
                if hb_list
                else None,
                "availability": [
                    1 if hb.get("status") in (1, "1") else 0
                    for hb in hb_list[-30:]
                ],
            }
        )

    payload = json.dumps({"locations": items}, ensure_ascii=False, default=str)
    if redis_client:
        try:
            await redis_client.setex(cache_key, 300, payload.encode("utf-8"))
        except Exception as e:
            log.warning("Locations cache write failed: %r", e)

    return web.Response(
        body=payload,
        content_type="application/json",
        status=200,
    )


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
        if not isinstance(panel_user, dict):
            log.warning(
                "Panel user data unavailable for user %s (panel_user_uuid=%s)",
                user_id,
                user.panel_user_uuid,
            )
            return _error("Failed to retrieve connection info", 502)
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

    if provider not in {"yookassa", "stars", "cryptopay", "freekassa", "platega", "severpay"}:
        return _error(f"Provider '{provider}' not supported via Mini App", 400)

    sale_mode = "traffic" if (gb is not None and not months) else "subscription"
    value = gb if sale_mode == "traffic" else months

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

        if price is None:
            return _error("Invalid plan selected")

        if sale_mode == "traffic":
            desc = f"Nova VPN — {value:g} GB"
        else:
            desc = f"Nova VPN — {int(value)} мес."

        metadata = {
            "user_id": user_id,
            "subscription_months": months,
            "traffic_gb": gb,
            "sale_mode": sale_mode,
        }

        try:
            if provider == "yookassa":
                svc = request.app.get("yookassa_service")
                if not svc:
                    return _error("Yookassa not configured", 503)
                payment = await svc.create_payment(
                    amount=float(price),
                    currency="RUB",
                    description=desc,
                    metadata=metadata,
                )
                if not payment:
                    return _error("Payment creation failed", 502)
                return _json({
                    "payment_id": payment.get("id", ""),
                    "payment_url": payment.get("confirmation_url"),
                    "invoice_link": None,
                    "provider": provider,
                })

            if provider == "stars":
                bot = request.app["bot"]
                invoice = await bot.create_invoice_link(
                    title="Nova VPN",
                    description=desc,
                    payload=f"miniapp_{user_id}_{value}",
                    currency="XTR",
                    prices=[{"label": "Nova VPN", "amount": int(stars_price or 1)}],
                )
                return _json({
                    "payment_id": "",
                    "payment_url": None,
                    "invoice_link": invoice,
                    "provider": provider,
                })

            if provider == "cryptopay":
                svc = request.app.get("cryptopay_service")
                if not svc:
                    return _error("CryptoPay not configured", 503)
                invoice_url = await svc.create_invoice(
                    session=session,
                    user_id=user_id,
                    months=value,
                    amount=float(price),
                    description=desc,
                    sale_mode=sale_mode,
                    promo_code_service=request.app.get("promo_code_service"),
                )
                if not invoice_url:
                    return _error("Payment creation failed", 502)
                return _json({
                    "payment_id": "",
                    "payment_url": invoice_url,
                    "invoice_link": None,
                    "provider": provider,
                })

            status_map = {
                "freekassa": "pending_freekassa",
                "platega": "pending_platega",
                "severpay": "pending_severpay",
            }
            payment_record = await payment_dal.create_payment_record(
                session,
                {
                    "user_id": user_id,
                    "amount": float(price),
                    "original_amount": None,
                    "discount_applied": None,
                    "currency": "RUB",
                    "status": status_map[provider],
                    "description": desc,
                    "subscription_duration_months": int(value),
                    "provider": provider,
                    "promo_code_id": None,
                },
            )
            await session.commit()

            if provider == "freekassa":
                svc = request.app.get("freekassa_service")
                if not svc:
                    return _error("FreeKassa not configured", 503)
                ok, resp = await svc.create_order(
                    payment_db_id=payment_record.payment_id,
                    user_id=user_id,
                    months=value,
                    amount=float(price),
                    currency=svc.default_currency,
                    ip_address=svc.server_ip,
                    payment_method_id=svc.payment_method_id,
                    extra_params={"us_method": svc.payment_method_id},
                    promo_code_service=request.app.get("promo_code_service"),
                    session=session,
                )
                if not ok:
                    return _error("Payment creation failed", 502)
                provider_identifier = resp.get("orderHash") or resp.get("orderId")
                if provider_identifier:
                    await payment_dal.update_provider_payment_and_status(
                        session, payment_record.payment_id, str(provider_identifier), payment_record.status
                    )
                    await session.commit()
                return _json({
                    "payment_id": str(payment_record.payment_id),
                    "payment_url": resp.get("location"),
                    "invoice_link": None,
                    "provider": provider,
                })

            if provider == "platega":
                svc = request.app.get("platega_service")
                if not svc:
                    return _error("Platega not configured", 503)
                payload_meta = json.dumps(
                    {
                        "payment_db_id": payment_record.payment_id,
                        "user_id": user_id,
                        "months": value,
                        "sale_mode": sale_mode,
                    }
                )
                ok, resp = await svc.create_transaction(
                    payment_db_id=payment_record.payment_id,
                    user_id=user_id,
                    months=value,
                    amount=float(price),
                    currency="RUB",
                    description=desc,
                    payload=payload_meta,
                    promo_code_service=request.app.get("promo_code_service"),
                    session=session,
                )
                if not ok:
                    return _error("Payment creation failed", 502)
                provider_identifier = resp.get("transactionId") or resp.get("id")
                provider_status = resp.get("status", payment_record.status)
                if provider_identifier:
                    await payment_dal.update_provider_payment_and_status(
                        session, payment_record.payment_id, str(provider_identifier), str(provider_status)
                    )
                    await session.commit()
                return _json({
                    "payment_id": str(payment_record.payment_id),
                    "payment_url": resp.get("redirect") or resp.get("url") or resp.get("paymentUrl"),
                    "invoice_link": None,
                    "provider": provider,
                })

            if provider == "severpay":
                svc = request.app.get("severpay_service")
                if not svc:
                    return _error("SeverPay not configured", 503)
                ok, resp = await svc.create_payment(
                    payment_db_id=payment_record.payment_id,
                    user_id=user_id,
                    months=value,
                    amount=float(price),
                    currency="RUB",
                    description=desc,
                    promo_code_service=request.app.get("promo_code_service"),
                    session=session,
                )
                if not ok:
                    return _error("Payment creation failed", 502)
                provider_identifier = resp.get("id") or resp.get("uid")
                if provider_identifier:
                    await payment_dal.update_provider_payment_and_status(
                        session, payment_record.payment_id, str(provider_identifier), payment_record.status
                    )
                    await session.commit()
                return _json({
                    "payment_id": str(payment_record.payment_id),
                    "payment_url": resp.get("url") or resp.get("payment_url") or resp.get("paymentUrl"),
                    "invoice_link": None,
                    "provider": provider,
                })

            return _error(f"Provider '{provider}' not supported via Mini App", 400)
        except Exception as e:
            await session.rollback()
            log.error(
                "Payment creation failed for user %s provider %s: %s",
                user_id,
                provider,
                e,
                exc_info=True,
            )
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
