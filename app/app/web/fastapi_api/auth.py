import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.app.web.api.auth import validate_init_data, validate_login_widget_data
from app.app.web.api.jwt_utils import create_jwt, verify_jwt
from app.app.web.fastapi_api.deps import CurrentUserDep, get_session
from app.database.dal import user_dal
from app.database.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/telegram")
async def auth_by_telegram(request: Request, session: AsyncSession = Depends(get_session)):
    body = await request.json()
    payload = body.get("telegram_user")
    settings = request.app.state.settings
    tg_user = validate_login_widget_data(payload, settings.BOT_TOKEN)
    if not tg_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram auth data")

    user_id: int = tg_user["id"]
    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        user, _ = await user_dal.create_user(
            session,
            {
                "user_id": user_id,
                "username": tg_user.get("username"),
                "first_name": tg_user.get("first_name"),
                "last_name": tg_user.get("last_name"),
                "language_code": "ru",
            },
        )
    else:
        user.username = tg_user.get("username")
        user.first_name = tg_user.get("first_name")
        user.last_name = tg_user.get("last_name")

    await session.commit()
    token = create_jwt(user_id, settings.WEB_SECRET_KEY)
    return {"token": token, "user_id": user_id}


@router.post("/access-link-login")
async def login_by_access_link(request: Request, session: AsyncSession = Depends(get_session)):
    body = await request.json()
    access_uuid = str(body.get("uuid") or "").strip()
    if not access_uuid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="uuid is required")

    settings = request.app.state.settings
    result = await session.execute(select(User).where(User.access_link_uuid == access_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access link")

    token = create_jwt(user.user_id, settings.WEB_SECRET_KEY)
    return {"token": token, "user_id": user.user_id}


@router.get("/access-link")
async def get_access_link(
    request: Request,
    session: AsyncSession = Depends(get_session),
    tg_user: dict = CurrentUserDep,
):
    user_id: int = tg_user["id"]

    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.access_link_uuid:
        user.access_link_uuid = str(uuid.uuid4())
        await session.commit()

    settings = request.app.state.settings
    app_base = (settings.MINI_APP_URL or "").strip().rstrip("/")
    if not app_base:
        origin = f"{request.url.scheme}://{request.headers.get('host', '')}"
        app_base = f"{origin}/app"

    return {
        "uuid": user.access_link_uuid,
        "url": f"{app_base}/th/{user.access_link_uuid}",
    }


@router.post("/link-telegram")
async def link_telegram(request: Request, session: AsyncSession = Depends(get_session)):
    settings = request.app.state.settings

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT token required")
    user_id = verify_jwt(auth_header[7:], settings.WEB_SECRET_KEY)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    init_data = request.headers.get("X-Telegram-Init-Data", "")
    tg_user = validate_init_data(init_data, settings.BOT_TOKEN)
    if not tg_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram initData")

    tg_id: int = tg_user["id"]

    existing = await user_dal.get_user_by_id(session, tg_id)
    if existing and existing.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Telegram account is already linked to another profile",
        )

    user = await user_dal.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_id != tg_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot relink: user_id mismatch")

    return {"ok": True}
