import json
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.app.web.fastapi_api.deps import get_current_user, get_session
from app.cache.redis_client import get_redis_client
from app.database.dal import subscription_dal, user_dal
from app.database.dal.active_discount_dal import get_active_discount
from app.database.dal import payment_dal
from app.database.models import Payment, Subscription, User
from app.logging_config import get_logger

router = APIRouter(prefix="/api", tags=["cabinet"])
logger = get_logger(__name__)


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


def _is_telegram_linked_user(user: User) -> bool:
    return bool(user.first_name or user.last_name or user.username)


@router.get("/user/me")
async def get_me(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])
    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    sub = await subscription_dal.get_active_subscription_by_user_id(session, user_id)
    has_any = await subscription_dal.has_any_subscription_for_user(session, user_id)
    settings = request.app.state.settings

    trial_available = (
        settings.TRIAL_ENABLED
        and not has_any
        and not user.is_banned
        and _is_telegram_linked_user(user)
    )

    return {
        "user_id": user.user_id,
        "first_name": user.first_name or current_user.get("first_name", ""),
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
    }


@router.get("/plans")
async def get_plans(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])
    settings = request.app.state.settings

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
        plans.append(
            {
                "months": months,
                "price_rub": rub_price,
                "price_stars": stars_price,
                "enabled": bool(enabled and has_price),
                "is_popular": months == 6,
                "is_best_value": months == 12,
            }
        )

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

    return {
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
    }


@router.get("/referral")
async def get_referral(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])
    settings = request.app.state.settings

    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    referral_code = await user_dal.ensure_referral_code(session, user)
    await session.commit()

    referred_count_result = await session.execute(
        select(func.count()).where(User.referred_by_id == user_id)
    )
    referred_count = referred_count_result.scalar() or 0

    purchased_result = await session.execute(
        select(func.count(Payment.payment_id.distinct()))
        .join(User, User.user_id == Payment.user_id)
        .where(User.referred_by_id == user_id, Payment.status == "succeeded")
    )
    purchased_count = purchased_result.scalar() or 0

    bot_username = request.app.state.bot_username or ""
    referral_link = f"https://t.me/{bot_username}?start=ref_{referral_code}" if bot_username else ""

    bonus_structure = {}
    for months in [1, 3, 6, 12]:
        inviter_days = settings.referral_bonus_inviter.get(months, 0)
        referee_days = settings.referral_bonus_referee.get(months, 0)
        bonus_structure[str(months)] = {
            "inviter_days": inviter_days,
            "referee_days": referee_days,
        }

    return {
        "referral_code": referral_code,
        "referral_link": referral_link,
        "referred_count": referred_count,
        "purchased_count": purchased_count,
        "bonus_structure": bonus_structure,
    }


@router.get("/operations")
async def get_operations_history(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])

    payments_result = await session.execute(
        select(Payment)
        .where(
            Payment.user_id == user_id,
            Payment.status == "succeeded",
            Payment.subscription_duration_months.is_not(None),
            Payment.subscription_duration_months > 0,
        )
        .order_by(Payment.created_at.desc())
    )
    payments = payments_result.scalars().all()

    trials_result = await session.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            and_(
                Subscription.status_from_panel == "TRIAL",
                Subscription.duration_months == 0,
            ),
        )
        .order_by(Subscription.start_date.desc())
    )
    trials = trials_result.scalars().all()

    operations: list[dict[str, Any]] = []

    for trial in trials:
        operations.append(
            {
                "type": "trial_activated",
                "created_at": trial.start_date.isoformat() if trial.start_date else None,
                "end_date": trial.end_date.isoformat() if trial.end_date else None,
                "duration_days": (
                    max(1, (trial.end_date - trial.start_date).days)
                    if trial.start_date and trial.end_date
                    else None
                ),
            }
        )

    for payment in payments:
        operations.append(
            {
                "type": "plan_payment",
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "amount": payment.amount,
                "currency": payment.currency,
                "provider": payment.provider,
                "months": payment.subscription_duration_months,
                "description": payment.description or "",
            }
        )

    operations.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {"operations": operations}


@router.get("/proxies")
async def get_proxies(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _ = current_user
    settings = request.app.state.settings
    proxies = [
        {
            "country": proxy.country,
            "emoji": proxy.emoji,
            "link": proxy.link,
        }
        for proxy in (settings.PROXIES or [])
        if proxy.link
    ]
    return {"proxies": proxies}


async def _fetch_json(url: str) -> dict[str, Any] | list[Any] | None:
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        if response.status_code != 200:
            return None
        return response.json()


@router.get("/locations")
async def get_locations(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _ = current_user
    settings = request.app.state.settings
    status_url = (settings.UPTIME_KUMA_STATUS_URL or "").strip()
    if not status_url:
        return {"locations": []}

    redis_client = get_redis_client()
    cache_key = f"miniapp:locations:{status_url}"
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                if isinstance(cached, bytes):
                    return json.loads(cached.decode("utf-8"))
                if isinstance(cached, str):
                    return json.loads(cached)
        except Exception as exc:
            logger.warning("Locations cache read failed", error=str(exc))

    try:
        status_data = await _fetch_json(status_url)
    except Exception as exc:
        logger.warning("Failed to fetch Uptime Kuma status", url=status_url, error=str(exc))
        return {"locations": []}

    if not isinstance(status_data, dict):
        return {"locations": []}

    monitors: list[dict[str, Any]] = []
    for group in status_data.get("publicGroupList", []) or []:
        group_name = str(group.get("name") or "")
        for mon in group.get("monitorList", []) or []:
            if isinstance(mon, dict):
                monitors.append({**mon, "_group": group_name})

    if not monitors and isinstance(status_data.get("monitors"), list):
        monitors = [m for m in status_data.get("monitors", []) if isinstance(m, dict)]

    heartbeat_url = status_url.replace("/api/status-page/", "/api/status-page/heartbeat/")
    heartbeat_data: dict[str, Any] | list[Any] | None = None
    try:
        heartbeat_data = await _fetch_json(heartbeat_url)
    except Exception as exc:
        logger.warning("Failed to fetch Uptime Kuma heartbeat", url=heartbeat_url, error=str(exc))

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
        status_val = latest_hb.get("status") if latest_hb is not None else mon.get("status")
        if status_val in (1, "1", "up", "UP", "online", "ONLINE", "ok", "OK"):
            status = "online"
        elif status_val in (0, "0", "down", "DOWN", "offline", "OFFLINE"):
            status = "offline"
        elif status_val in (2, "2", "pending", "PENDING"):
            status = "pending"

        ping_raw = latest_hb.get("ping") if latest_hb is not None else mon.get("ping")
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
                    (sum(1 for hb in hb_list if hb.get("status") in (1, "1")) / len(hb_list) * 100),
                    1,
                )
                if hb_list
                else None,
                "availability": [1 if hb.get("status") in (1, "1") else 0 for hb in hb_list[-30:]],
            }
        )

    payload = {"locations": items}
    if redis_client:
        try:
            await redis_client.setex(cache_key, 300, json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        except Exception as exc:
            logger.warning("Locations cache write failed", error=str(exc))

    return payload


@router.post("/promo/apply")
async def apply_promo(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])
    body = await request.json()
    code: str = str(body.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code is required")

    promo_service = request.app.state.promo_code_service
    if not promo_service:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable")

    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    lang = user.language_code or "ru"
    success, result = await promo_service.apply_promo_code(session, user_id, code, lang)
    if success:
        new_end = result
        if isinstance(new_end, datetime):
            if new_end.tzinfo is None:
                new_end = new_end.replace(tzinfo=timezone.utc)
            await session.commit()
            return {"success": True, "type": "bonus_days", "new_end_date": new_end.isoformat()}

    ok2, res2 = await promo_service.apply_discount_promo_code(session, user_id, code, lang)
    if ok2:
        discount_row = await get_active_discount(session, user_id)
        expires = None
        if discount_row and discount_row.expires_at:
            expires = discount_row.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
        await session.commit()
        return {
            "success": True,
            "type": "discount",
            "discount_percentage": res2,
            "expires_at": expires.isoformat() if expires else None,
        }

    await session.rollback()
    return {"success": False, "error": result if isinstance(result, str) else "not_found"}


@router.get("/subscription/connect")
async def get_connect(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])
    sub_service = request.app.state.subscription_service
    panel_service = request.app.state.panel_service
    if not sub_service or not panel_service:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable")

    user = await user_dal.get_user_by_id(session, user_id)
    if not user or not user.panel_user_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")
    sub = await subscription_dal.get_active_subscription_by_user_id(session, user_id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription")

    panel_user = await panel_service.get_user_by_uuid(user.panel_user_uuid)
    if not isinstance(panel_user, dict):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to retrieve connection info")
    sub_url = panel_user.get("subscriptionUrl", "")
    return {"connect_url": sub_url, "config_link": sub_url}


@router.post("/payment/create")
async def create_payment(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])
    body = await request.json()
    months = body.get("months")
    gb = body.get("gb")
    provider = str(body.get("provider") or "")
    if not provider:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider is required")
    if not months and not gb:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="months or gb is required")

    settings = request.app.state.settings
    if provider not in {"yookassa", "stars", "cryptopay", "freekassa", "platega", "severpay"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider '{provider}' not supported via Mini App")

    sale_mode = "traffic" if (gb is not None and not months) else "subscription"
    value = gb if sale_mode == "traffic" else months

    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    discount = await get_active_discount(session, user_id)
    discount_pct = discount.discount_percentage if discount else 0

    if months:
        base_price = settings.subscription_options.get(months)
        stars_price = settings.stars_subscription_options.get(months)
    else:
        base_price = settings.traffic_packages.get(gb)
        stars_price = settings.stars_traffic_packages.get(gb)

    if base_price is None and provider != "stars":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan selected")

    if provider == "stars":
        price = stars_price
    else:
        price = base_price
        if discount_pct and price:
            price = int(price * (1 - discount_pct / 100))
    if price is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan selected")

    desc = f"KLAR VPN — {value:g} GB" if sale_mode == "traffic" else f"KLAR VPN — {int(value)} мес."
    metadata = {"user_id": user_id, "subscription_months": months, "traffic_gb": gb, "sale_mode": sale_mode}

    if provider == "yookassa":
        svc = request.app.state.yookassa_service
        if not svc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Yookassa not configured")
        payment = await svc.create_payment(amount=float(price), currency="RUB", description=desc, metadata=metadata)
        if not payment:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment creation failed")
        return {"payment_id": payment.get("id", ""), "payment_url": payment.get("confirmation_url"), "invoice_link": None, "provider": provider}

    if provider == "stars":
        bot = request.app.state.bot
        invoice = await bot.create_invoice_link(
            title="KLAR VPN",
            description=desc,
            payload=f"miniapp_{user_id}_{value}",
            currency="XTR",
            prices=[{"label": "KLAR VPN", "amount": int(stars_price or 1)}],
        )
        return {"payment_id": "", "payment_url": None, "invoice_link": invoice, "provider": provider}

    if provider == "cryptopay":
        svc = request.app.state.cryptopay_service
        if not svc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="CryptoPay not configured")
        invoice_url = await svc.create_invoice(
            session=session,
            user_id=user_id,
            months=value,
            amount=float(price),
            description=desc,
            sale_mode=sale_mode,
            promo_code_service=request.app.state.promo_code_service,
        )
        if not invoice_url:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment creation failed")
        return {"payment_id": "", "payment_url": invoice_url, "invoice_link": None, "provider": provider}

    status_map = {"freekassa": "pending_freekassa", "platega": "pending_platega", "severpay": "pending_severpay"}
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
        svc = request.app.state.freekassa_service
        if not svc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="FreeKassa not configured")
        ok, resp = await svc.create_order(
            payment_db_id=payment_record.payment_id,
            user_id=user_id,
            months=value,
            amount=float(price),
            currency=svc.default_currency,
            ip_address=svc.server_ip,
            payment_method_id=svc.payment_method_id,
            extra_params={"us_method": svc.payment_method_id},
            promo_code_service=request.app.state.promo_code_service,
            session=session,
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment creation failed")
        return {"payment_id": str(payment_record.payment_id), "payment_url": resp.get("location"), "invoice_link": None, "provider": provider}

    if provider == "platega":
        svc = request.app.state.platega_service
        if not svc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Platega not configured")
        payload_meta = json.dumps({"payment_db_id": payment_record.payment_id, "user_id": user_id, "months": value, "sale_mode": sale_mode})
        ok, resp = await svc.create_transaction(
            payment_db_id=payment_record.payment_id,
            user_id=user_id,
            months=value,
            amount=float(price),
            currency="RUB",
            description=desc,
            payload=payload_meta,
            promo_code_service=request.app.state.promo_code_service,
            session=session,
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment creation failed")
        return {"payment_id": str(payment_record.payment_id), "payment_url": resp.get("redirect") or resp.get("url") or resp.get("paymentUrl"), "invoice_link": None, "provider": provider}

    if provider == "severpay":
        svc = request.app.state.severpay_service
        if not svc:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="SeverPay not configured")
        ok, resp = await svc.create_payment(
            payment_db_id=payment_record.payment_id,
            user_id=user_id,
            months=value,
            amount=float(price),
            currency="RUB",
            description=desc,
            promo_code_service=request.app.state.promo_code_service,
            session=session,
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment creation failed")
        return {"payment_id": str(payment_record.payment_id), "payment_url": resp.get("url") or resp.get("payment_url") or resp.get("paymentUrl"), "invoice_link": None, "provider": provider}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Provider '{provider}' not supported via Mini App")


@router.post("/payment/trial")
async def activate_trial(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    user_id: int = int(current_user["id"])
    settings = request.app.state.settings
    auth_source = current_user.get("_auth_source")
    if not settings.TRIAL_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial is not enabled")

    sub_service = request.app.state.subscription_service
    if not sub_service:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unavailable")

    has_any = await subscription_dal.has_any_subscription_for_user(session, user_id)
    if has_any:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial already used")
    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if auth_source != "telegram_init" and not _is_telegram_linked_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial is available only for Telegram-linked accounts")

    result = await sub_service.activate_trial_subscription(session, user_id)
    if not result or not result.get("eligible"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trial already used")
    if not result.get("activated"):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Trial activation failed")

    end_date = result.get("end_date")
    return {"success": True, "end_date": end_date.isoformat() if end_date else None}
