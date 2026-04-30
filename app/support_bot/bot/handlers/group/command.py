from contextlib import suppress

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, MagicData
from aiogram.types import Message
from aiogram.utils.markdown import hcode

from app.support_bot.bot.manager import Manager
from app.support_bot.bot.utils.create_forum_topic import set_ticket_topic_state
from app.support_bot.bot.utils.redis import RedisStorage
from app.support_bot.bot.utils.vpn_user_info import build_support_user_info_message

router_id = Router()
router_id.message.filter(
    F.chat.type.in_(["group", "supergroup"]),
)


@router_id.message(Command("id"))
async def handler(message: Message) -> None:
    """
    Sends chat ID in response to the /id command.

    :param message: Message object.
    :return: None
    """
    await message.reply(hcode(message.chat.id))


router = Router()
router.message.filter(
    F.message_thread_id.is_not(None),
    F.chat.type.in_(["group", "supergroup"]),
    MagicData(F.event_chat.id == F.config.bot.GROUP_ID),  # type: ignore
)


@router.message(Command("silent"))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Toggles silent mode for a user in the group.
    If silent mode is disabled, it will be enabled, and vice versa.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data: return None  # noqa

    if user_data.message_silent_mode:
        text = manager.text_message.get("silent_mode_disabled")
        with suppress(TelegramBadRequest):
            # Reply with the specified text
            await message.reply(text)

            # Unpin the chat message with the silent mode status
            await message.bot.unpin_chat_message(
                chat_id=message.chat.id,
                message_id=user_data.message_silent_id,
            )

        user_data.message_silent_mode = False
        user_data.message_silent_id = None
    else:
        text = manager.text_message.get("silent_mode_enabled")
        with suppress(TelegramBadRequest):
            # Reply with the specified text
            msg = await message.reply(text)

            # Pin the chat message with the silent mode status
            await msg.pin(disable_notification=True)

        user_data.message_silent_mode = True
        user_data.message_silent_id = msg.message_id

    await redis.update_user(user_data.id, user_data)


@router.message(Command("information"))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Sends user information in response to the /information command.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data: return None  # noqa

    user_info_text = await build_support_user_info_message(user_data.id)
    commands_help_text = manager.text_message.get("user_information")

    await message.reply(
        f"{user_info_text}\n\n{commands_help_text}",
        disable_web_page_preview=True,
    )


@router.message(Command(commands=["ban"]))
async def handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    """
    Toggles the ban status for a user in the group.
    If the user is banned, they will be unbanned, and vice versa.

    :param message: Message object.
    :param manager: Manager object.
    :param redis: RedisStorage object.
    :return: None
    """
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data: return None  # noqa

    if user_data.is_banned:
        user_data.is_banned = False
        text = manager.text_message.get("user_unblocked")
    else:
        user_data.is_banned = True
        text = manager.text_message.get("user_blocked")

    # Reply with the specified text
    await message.reply(text)
    await redis.update_user(user_data.id, user_data)


@router.message(Command("close"))
async def close_ticket_handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return
    if message.from_user is None or message.from_user.id not in manager.config.bot.DEV_IDS:
        return

    try:
        await set_ticket_topic_state(message.bot, manager.config, user_data, False)
    except Exception as exc:
        await message.reply(f"⚠️ Не удалось переименовать тему: <code>{exc}</code>")
        return

    was_open = user_data.ticket_open
    user_data.ticket_open = False
    await redis.update_user(user_data.id, user_data)
    if was_open:
        await message.reply("🔴 <b>Тикет закрыт.</b>")
    else:
        await message.reply("🔴 Тикет уже был закрыт, статус темы обновлен.")


@router.message(Command("open"))
async def open_ticket_handler(message: Message, manager: Manager, redis: RedisStorage) -> None:
    user_data = await redis.get_by_message_thread_id(message.message_thread_id)
    if not user_data:
        return
    if message.from_user is None or message.from_user.id not in manager.config.bot.DEV_IDS:
        return

    try:
        await set_ticket_topic_state(message.bot, manager.config, user_data, True)
    except Exception as exc:
        await message.reply(f"⚠️ Не удалось переименовать тему: <code>{exc}</code>")
        return

    was_open = user_data.ticket_open
    user_data.ticket_open = True
    await redis.update_user(user_data.id, user_data)
    if was_open:
        await message.reply("🟢 Тикет уже был открыт, статус темы обновлен.")
    else:
        await message.reply("🟢 <b>Тикет открыт.</b>")
