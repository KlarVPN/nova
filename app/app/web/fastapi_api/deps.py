from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.app.web.api.auth import validate_init_data
from app.app.web.api.jwt_utils import verify_jwt


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_factory = request.app.state.async_session_factory
    async with session_factory() as session:
        yield session


def get_settings(request: Request):
    return request.app.state.settings


async def get_current_user(
    request: Request,
    x_telegram_init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    authorization: str | None = Header(default=None),
):
    settings = request.app.state.settings

    if x_telegram_init_data:
        tg_user = validate_init_data(x_telegram_init_data, settings.BOT_TOKEN)
        if tg_user:
            return tg_user

    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        user_id = verify_jwt(token, settings.WEB_SECRET_KEY)
        if user_id:
            return {"id": user_id}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


SessionDep = Depends(get_session)
CurrentUserDep = Depends(get_current_user)
