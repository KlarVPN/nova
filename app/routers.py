from aiogram import Router, F

from app.handlers.user import user_router_aggregate
from app.handlers import inline_mode
from app.config import Settings


def build_root_router(settings: Settings) -> Router:
    root = Router(name="root")

    # Allow all updates only in private chats (messages, callback queries, etc.)
    root.message.filter(F.chat.type == "private")
    root.callback_query.filter(F.message.chat.type == "private")

    # Public routers
    root.include_router(user_router_aggregate)
    root.include_router(inline_mode.router)

    return root
