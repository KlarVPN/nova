import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.app.web.fastapi_api.deps import get_current_admin, get_session
from app.database.dal import ad_dal, message_log_dal, payment_dal, panel_sync_dal, promo_code_dal, user_dal
from app.handlers.admin.sync_admin import perform_sync
from app.utils.message_queue import get_queue_manager

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/overview")
async def admin_overview(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    user_stats = await user_dal.get_enhanced_user_statistics(session)
    financial_stats = await payment_dal.get_financial_statistics(session)
    sync_status = await panel_sync_dal.get_panel_sync_status(session)

    queue_manager = get_queue_manager()
    queue_stats = queue_manager.get_queue_stats() if queue_manager else None

    return {
        "user_stats": user_stats,
        "financial_stats": financial_stats,
        "sync_status": {
            "last_sync_time": sync_status.last_sync_time.isoformat() if sync_status and sync_status.last_sync_time else None,
            "status": sync_status.status if sync_status else "never_run",
            "details": sync_status.details if sync_status else "",
            "users_processed_from_panel": sync_status.users_processed_from_panel if sync_status else 0,
            "subscriptions_synced": sync_status.subscriptions_synced if sync_status else 0,
        },
        "queue_stats": queue_stats,
    }


@router.get("/payments")
async def admin_payments(
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = page * page_size
    items = await payment_dal.get_recent_payment_logs_with_user(session, limit=page_size, offset=offset)
    total = await payment_dal.get_payments_count(session)
    return {
        "total": total,
        "items": [
            {
                "payment_id": p.payment_id,
                "user_id": p.user_id,
                "username": p.user.username if p.user else None,
                "first_name": p.user.first_name if p.user else None,
                "amount": p.amount,
                "currency": p.currency,
                "status": p.status,
                "provider": p.provider,
                "months": p.subscription_duration_months,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in items
        ],
    }


@router.get("/payments.csv")
async def admin_payments_csv(
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    all_payments = await payment_dal.get_all_succeeded_payments_with_user(session)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "payment_id",
        "user_id",
        "username",
        "first_name",
        "amount",
        "currency",
        "provider",
        "status",
        "description",
        "units",
        "created_at",
        "provider_payment_id",
    ])

    for payment in all_payments:
        writer.writerow([
            payment.payment_id,
            payment.user_id,
            payment.user.username if payment.user and payment.user.username else "",
            payment.user.first_name if payment.user and payment.user.first_name else "",
            payment.amount,
            payment.currency,
            payment.provider or "",
            payment.status,
            payment.description or "",
            payment.subscription_duration_months or "",
            payment.created_at.isoformat() if payment.created_at else "",
            payment.provider_payment_id or "",
        ])

    content = output.getvalue()
    output.close()
    filename = f"payments_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([content.encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/users")
async def admin_users(
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
):
    users = await user_dal.get_all_users_paginated(session, page=page, page_size=page_size)
    total = await user_dal.count_all_users(session)
    return {
        "total": total,
        "items": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "first_name": u.first_name,
                "avatar_url": u.telegram_photo_url,
                "is_banned": u.is_banned,
                "registration_date": u.registration_date.isoformat() if u.registration_date else None,
            }
            for u in users
        ],
    }


@router.post("/users/{user_id}/ban")
async def admin_ban_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_dal.update_user(session, user_id, {"is_banned": True})
    await session.commit()
    return {"ok": True}


@router.post("/users/{user_id}/unban")
async def admin_unban_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await user_dal.update_user(session, user_id, {"is_banned": False})
    await session.commit()
    return {"ok": True}


@router.post("/sync")
async def admin_sync(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    panel_service = request.app.state.panel_service
    settings = request.app.state.settings
    i18n = request.app.state.i18n_instance

    if panel_service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Panel service is unavailable")

    result = await perform_sync(
        panel_service=panel_service,
        session=session,
        settings=settings,
        i18n_instance=i18n,
    )
    await session.commit()
    return result


@router.get("/promos")
async def admin_promos(
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
):
    offset = page * page_size
    items = await promo_code_dal.get_all_promo_codes_with_details(session, limit=page_size, offset=offset)
    total = await promo_code_dal.get_promo_codes_count(session)
    return {
        "total": total,
        "items": [
            {
                "promo_code_id": p.promo_code_id,
                "code": p.code,
                "promo_type": p.promo_type,
                "bonus_days": p.bonus_days,
                "discount_percentage": p.discount_percentage,
                "max_activations": p.max_activations,
                "current_activations": p.current_activations,
                "is_active": p.is_active,
                "valid_until": p.valid_until.isoformat() if p.valid_until else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in items
        ],
    }


@router.post("/promos")
async def admin_create_promo(
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    code = str(payload.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Promo code is required")

    promo_type = str(payload.get("promo_type") or "bonus_days").strip()
    if promo_type not in {"bonus_days", "discount"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid promo_type")

    valid_until = None
    raw_valid_until = payload.get("valid_until")
    if raw_valid_until:
        try:
            valid_until = datetime.fromisoformat(str(raw_valid_until).replace("Z", "+00:00"))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid valid_until") from exc

    promo_data = {
        "code": code,
        "promo_type": promo_type,
        "bonus_days": int(payload.get("bonus_days") or 0),
        "discount_percentage": int(payload.get("discount_percentage") or 0),
        "max_activations": int(payload.get("max_activations") or 1),
        "current_activations": 0,
        "is_active": bool(payload.get("is_active", True)),
        "created_by_admin_id": int(_admin["id"]),
        "valid_until": valid_until,
    }

    existing = await promo_code_dal.get_promo_code_by_code(session, code)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promo code already exists")

    promo = await promo_code_dal.create_promo_code(session, promo_data)
    await session.commit()
    return {"promo_code_id": promo.promo_code_id, "code": promo.code}


@router.patch("/promos/{promo_id}")
async def admin_update_promo(
    promo_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    update_data: dict = {}
    allowed = {
        "code",
        "promo_type",
        "bonus_days",
        "discount_percentage",
        "max_activations",
        "current_activations",
        "is_active",
        "valid_until",
    }
    for key, value in payload.items():
        if key not in allowed:
            continue
        if key == "code" and isinstance(value, str):
            update_data[key] = value.strip().upper()
        elif key == "valid_until" and value:
            update_data[key] = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        else:
            update_data[key] = value

    promo = await promo_code_dal.update_promo_code(session, promo_id, update_data)
    if not promo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo not found")
    await session.commit()
    return {"ok": True}


@router.delete("/promos/{promo_id}")
async def admin_delete_promo(
    promo_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    promo = await promo_code_dal.delete_promo_code(session, promo_id)
    if not promo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo not found")
    await session.commit()
    return {"ok": True}


@router.get("/promos/{promo_id}/activations")
async def admin_promo_activations(
    promo_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=50, ge=1, le=200),
):
    offset = page * page_size
    total = await promo_code_dal.count_promo_activations_by_code_id(session, promo_id)
    activations = await promo_code_dal.get_promo_activations_by_code_id(
        session, promo_id, limit=page_size, offset=offset
    )
    return {
        "total": total,
        "items": [
            {
                "activation_id": a.activation_id,
                "user_id": a.user_id,
                "payment_id": a.payment_id,
                "activated_at": a.activated_at.isoformat() if a.activated_at else None,
            }
            for a in activations
        ],
    }


@router.get("/promos/{promo_id}/activations.csv")
async def admin_promo_activations_csv(
    promo_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    promo = await promo_code_dal.get_promo_code_by_id(session, promo_id)
    if not promo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo not found")
    activations = await promo_code_dal.get_promo_activations_by_code_id(session, promo_id, limit=None, offset=0)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["activation_id", "promo_code", "user_id", "payment_id", "activated_at"])
    for a in activations:
        writer.writerow([
            a.activation_id,
            promo.code,
            a.user_id,
            a.payment_id or "",
            a.activated_at.isoformat() if a.activated_at else "",
        ])

    content = output.getvalue()
    output.close()
    filename = f"promo_{promo.code}_activations.csv"
    return StreamingResponse(
        iter([content.encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/logs")
async def admin_logs(
    request: Request,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=50, ge=1, le=200),
    user_id: int | None = Query(default=None),
):
    offset = page * page_size
    settings = request.app.state.settings
    if user_id is not None:
        total = await message_log_dal.count_user_message_logs(session, user_id)
        logs = await message_log_dal.get_user_message_logs(session, user_id, page_size, offset)
    else:
        hide_admin_events = bool(getattr(settings, "LOG_ADMIN_HIDE", False))
        total = await message_log_dal.count_all_message_logs(session, hide_admin_events=hide_admin_events)
        logs = await message_log_dal.get_all_message_logs(
            session, page_size, offset, hide_admin_events=hide_admin_events
        )

    return {
        "total": total,
        "items": [
            {
                "message_log_id": l.log_id,
                "user_id": l.user_id,
                "target_user_id": l.target_user_id,
                "telegram_username": l.telegram_username,
                "telegram_first_name": l.telegram_first_name,
                "event_type": l.event_type,
                "content": l.content,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ],
    }


@router.get("/ads")
async def admin_ads(
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
    page: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items = await ad_dal.list_campaigns_paged(session, page=page, page_size=page_size)
    total = await ad_dal.count_campaigns(session)
    return {
        "total": total,
        "items": [
            {
                "ad_campaign_id": c.ad_campaign_id,
                "source": c.source,
                "start_param": c.start_param,
                "cost": c.cost,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in items
        ],
    }


@router.post("/ads")
async def admin_create_ad(
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    source = str(payload.get("source") or "").strip()
    start_param = str(payload.get("start_param") or "").strip()
    cost = float(payload.get("cost") or 0)
    if not source or not start_param:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="source and start_param are required")

    campaign = await ad_dal.create_campaign(session, source=source, start_param=start_param, cost=cost)
    await session.commit()
    return {"ad_campaign_id": campaign.ad_campaign_id}


@router.delete("/ads/{campaign_id}")
async def admin_delete_ad(
    campaign_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    deleted = await ad_dal.delete_campaign(session, campaign_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await session.commit()
    return {"ok": True}


@router.post("/ads/{campaign_id}/toggle")
async def admin_toggle_ad(
    campaign_id: int,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    is_active = bool(payload.get("is_active", True))
    updated = await ad_dal.toggle_campaign_active(session, campaign_id, is_active=is_active)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    await session.commit()
    return {"ok": True}


@router.get("/ads/{campaign_id}/stats")
async def admin_ad_stats(
    campaign_id: int,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    campaign = await ad_dal.get_campaign_by_id(session, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    stats = await ad_dal.get_campaign_stats(session, campaign_id)
    return {"campaign": {"ad_campaign_id": campaign.ad_campaign_id, "source": campaign.source}, "stats": stats}


@router.post("/broadcast")
async def admin_broadcast(
    payload: dict,
    request: Request,
    session: AsyncSession = Depends(get_session),
    _admin: dict = Depends(get_current_admin),
):
    text = str(payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text is required")

    target = str(payload.get("target") or "all").strip().lower()
    if target == "active":
        user_ids = await user_dal.get_user_ids_with_active_subscription(session)
    elif target == "inactive":
        user_ids = await user_dal.get_user_ids_without_active_subscription(session)
    else:
        user_ids = await user_dal.get_all_active_user_ids_for_broadcast(session)

    queue_manager = get_queue_manager()
    if not queue_manager:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Queue manager is unavailable")

    bot = request.app.state.bot
    if not bot:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Bot is unavailable")

    queued = 0
    for uid in user_ids:
        try:
            await queue_manager.send_message(
                chat_id=uid,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            queued += 1
        except Exception:
            continue

    return {"queued": queued, "target": target}
