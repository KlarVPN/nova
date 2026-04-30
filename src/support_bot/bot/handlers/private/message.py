from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.types import Message

from src.support_bot.bot.manager import Manager
from src.support_bot.bot.types.album import Album
from src.support_bot.bot.utils.create_forum_topic import (
    create_forum_topic,
    get_or_create_forum_topic,
    set_ticket_topic_state,
)
from src.support_bot.bot.utils.vpn_user_info import build_support_user_info_message
from src.support_bot.bot.utils.redis import RedisStorage
from src.support_bot.bot.utils.redis.models import UserData

router = Router()
router.message.filter(F.chat.type == "private", StateFilter(None))


async def send_user_information_to_topic(
        message: Message,
        manager: Manager,
        user_data: UserData,
) -> None:
    user_info_text = await build_support_user_info_message(user_data.id)
    commands_help_text = manager.text_message.get("user_information")
    text = f"{user_info_text}\n\n{commands_help_text}"
    await message.bot.send_message(
        chat_id=manager.config.bot.GROUP_ID,
        message_thread_id=user_data.message_thread_id,
        text=text,
        disable_web_page_preview=True,
    )


@router.edited_message()
async def handle_edited_message(message: Message, manager: Manager) -> None:
    """
    Handle edited messages.

    :param message: The edited message.
    :param manager: Manager object.
    :return: None
    """
    # Get the text for the edited message
    text = manager.text_message.get("message_edited")
    await message.reply(text)


@router.message(F.media_group_id)
@router.message(F.media_group_id.is_(None))
async def handle_incoming_message(
        message: Message,
        manager: Manager,
        redis: RedisStorage,
        user_data: UserData,
        album: Album | None = None,
) -> None:
    """
    Handles incoming messages and copies them to the forum topic.
    If the user is banned, the messages are ignored.

    :param message: The incoming message.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :param user_data: UserData object.
    :param album: Album object or None.
    :return: None
    """
    # Check if the user is banned
    if user_data.is_banned:
        return

    async def copy_message_to_topic():
        """
        Copies the message or album to the forum topic.
        If no album is provided, the message is copied. Otherwise, the album is copied.
        """
        has_thread = user_data.message_thread_id is not None
        message_thread_id = await get_or_create_forum_topic(
            message.bot,
            redis,
            manager.config,
            user_data,
        )

        if not has_thread:
            await send_user_information_to_topic(message, manager, user_data)

        if not user_data.ticket_open:
            user_data.ticket_open = True
            await set_ticket_topic_state(message.bot, manager.config, user_data, True)
            await redis.update_user(user_data.id, user_data)
            await message.bot.send_message(
                chat_id=manager.config.bot.GROUP_ID,
                message_thread_id=message_thread_id,
                text="🟢 <b>Тикет автоматически открыт:</b> пользователь снова написал в поддержку.",
            )

        if not album:
            await message.forward(
                chat_id=manager.config.bot.GROUP_ID,
                message_thread_id=message_thread_id,
            )
        else:
            await album.copy_to(
                chat_id=manager.config.bot.GROUP_ID,
                message_thread_id=message_thread_id,
            )

    try:
        await copy_message_to_topic()
    except TelegramBadRequest as ex:
        if "message thread not found" in ex.message:
            user_data.message_thread_id = await create_forum_topic(
                message.bot,
                manager.config,
                user_data.full_name,
            )
            await redis.update_user(user_data.id, user_data)
            await send_user_information_to_topic(message, manager, user_data)
            await copy_message_to_topic()
        else:
            raise

    text = manager.text_message.get("message_sent")
    await message.reply(text)
