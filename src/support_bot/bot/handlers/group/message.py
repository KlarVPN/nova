import asyncio
from typing import Optional

from aiogram import Router, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import MagicData
from aiogram.types import Message

from src.support_bot.bot.manager import Manager
from src.support_bot.bot.types.album import Album
from src.support_bot.bot.utils.redis import RedisStorage
from src.support_bot.bot.utils.vpn_user_info import build_support_user_info_message

router = Router()
router.message.filter(
    MagicData(F.event_chat.id == F.config.bot.GROUP_ID),  # type: ignore
    F.chat.type.in_(["group", "supergroup"]),
    F.message_thread_id.is_not(None),
)


@router.message(F.forum_topic_created)
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    await asyncio.sleep(3)
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data: return None  # noqa

    user_info_text = await build_support_user_info_message(user_data.id)
    commands_help_text = manager.text_message.get("user_information")
    text = f"{user_info_text}\n\n{commands_help_text}"

    message = await message.bot.send_message(
        chat_id=manager.config.bot.GROUP_ID,
        text=text,
        message_thread_id=user_data.message_thread_id
    )

    # Pin the message
    await message.pin()


@router.message(F.pinned_message | F.forum_topic_edited | F.forum_topic_closed | F.forum_topic_reopened)
async def handler(message: Message) -> None:
    """
    Delete service messages such as pinned, edited, closed, or reopened forum topics.

    :param message: Message object.
    :return: None
    """
    await message.delete()


@router.message(F.media_group_id, F.from_user[F.is_bot.is_(False)])
@router.message(F.media_group_id.is_(None), F.from_user[F.is_bot.is_(False)])
async def handler(message: Message, manager: Manager, redis: RedisStorage, album: Optional[Album] = None) -> None:
    """
    Handles user messages and sends them to the respective user.
    If silent mode is enabled for the user, the messages are ignored.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param album: Album object or None.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data: return None  # noqa

    # Forward messages to user only when admin replies in thread.
    if message.reply_to_message is None:
        return

    replied = message.reply_to_message
    is_reply_to_user_content = bool(getattr(replied, "forward_origin", None))
    if replied.from_user and not replied.from_user.is_bot and replied.from_user.id == user_data.id:
        is_reply_to_user_content = True
    if not is_reply_to_user_content:
        return

    if user_data.message_silent_mode:
        # If silent mode is enabled, ignore all messages.
        return

    text = manager.text_message.get("message_sent_to_user")

    try:
        if not album:
            await message.copy_to(chat_id=user_data.id)
        else:
            await album.copy_to(chat_id=user_data.id)

    except TelegramAPIError as ex:
        if "blocked" in ex.message:
            text = manager.text_message.get("blocked_by_user")

    except (Exception,):
        text = manager.text_message.get("message_not_sent")

    await message.reply(text)
