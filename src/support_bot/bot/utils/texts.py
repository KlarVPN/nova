from abc import abstractmethod, ABCMeta

from aiogram.utils.markdown import hbold

# Add other languages and their corresponding codes as needed.
# You can also keep only one language by removing the line with the unwanted language.
SUPPORTED_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}


class Text(metaclass=ABCMeta):
    """
    Abstract base class for handling text data in different languages.
    """

    def __init__(self, language_code: str) -> None:
        """
        Initializes the Text instance with the specified language code.

        :param language_code: The language code (e.g., "ru" or "en").
        """
        self.language_code = language_code if language_code in SUPPORTED_LANGUAGES.keys() else "en"

    @property
    @abstractmethod
    def data(self) -> dict:
        """
        Abstract property to be implemented by subclasses. Represents the language-specific text data.

        :return: Dictionary containing language-specific text data.
        """
        raise NotImplementedError

    def get(self, code: str) -> str:
        """
        Retrieves the text corresponding to the provided code in the current language.

        :param code: The code associated with the desired text.
        :return: The text in the current language.
        """
        return self.data[self.language_code][code]


class TextMessage(Text):
    """
    Subclass of Text for managing text messages in different languages.
    """

    @property
    def data(self) -> dict:
        """
        Provides language-specific text data for text messages.

        :return: Dictionary containing language-specific text data for text messages.
        """
        return {
            "en": {
                "select_language": f"👋 <b>Welcome to Klar Support</b>, {hbold('{full_name}')}!\n\n🌐 Please select your language:",
                "change_language": "<b>🌐 Select your language:</b>",
                "main_menu": "✍️ <b>Describe your issue</b>\n\nTo help you faster, please provide:\n\n• What device are you using VPN on?\n• Describe the problem in as much detail as possible\n• Send a screenshot of the error (if available)\n\n⏱ Response may take some time. Thank you for your patience!",
                "message_sent": "📦 <b>Your message has been sent to support!</b>\n\nWe've received your request and will get back to you soon.\n\n⏱ We typically respond within a few hours.\n\nThank you for your patience! 💙",
                "message_edited": (
                    "✏️ <b>The message was edited only in your chat.</b>\n\nTo send an edited message, send it as a new message."
                ),
                "user_started_bot": (
                    f"User {hbold('{name}')} started the bot!\n\n"
                    "List of available commands:\n\n"
                    "• /ban\n"
                    "Block/Unblock user"
                    "<blockquote>Block the user if you do not want to receive messages from him.</blockquote>\n\n"
                    "• /silent\n"
                    "Activate/Deactivate silent mode"
                    "<blockquote>When silent mode is enabled, messages are not sent to the user.</blockquote>\n\n"
                    "• /information\n"
                    "User information"
                    "<blockquote>Receive a message with basic information about the user.</blockquote>"
                ),
                "user_restarted_bot": f"User {hbold('{name}')} restarted the bot!",
                "user_stopped_bot": f"User {hbold('{name}')} stopped the bot!",
                "user_blocked": "<b>User blocked!</b> Messages from the user are not accepted.",
                "user_unblocked": "<b>User unblocked!</b> Messages from the user are being accepted again.",
                "blocked_by_user": "<b>Message not sent!</b> The bot has been blocked by the user.",
                "user_information": (
                    "<b>Краткая справка по командам:</b>\n\n"
                    "• <code>/ban</code> — блокировать или разблокировать пользователя.\n"
                    "• <code>/silent</code> — включить или выключить тихий режим.\n"
                    "• <code>/information</code> — показать эту краткую справку.\n"
                    "• <code>/close</code> — закрыть тикет (🔴).\n"
                    "• <code>/open</code> — открыть тикет (🟢)."
                ),
                "message_not_sent": "<b>Message not sent!</b> An unexpected error occurred.",
                "message_sent_to_user": "<b>Message sent to user!</b>",
                "silent_mode_enabled": (
                    "<b>Silent mode activated!</b> Messages will not be delivered to the user."
                ),
                "silent_mode_disabled": (
                    "<b>Silent mode deactivated!</b> The user will receive all messages."
                ),
            },
            "ru": {
                "select_language": f"👋 <b>Добро пожаловать в поддержку Klar</b>, {hbold('{full_name}')}!\n\n🌐 Пожалуйста, выберите ваш язык:",
                "change_language": "<b>🌐 Выберите ваш язык:</b>",
                "main_menu": "✍️ <b>Опишите вашу проблему</b>\n\nЧтобы мы могли помочь быстрее, пожалуйста, укажите:\n\n• На каком устройстве вы запускаете VPN?\n• Опишите проблему как можно подробнее\n• Пришлите скриншот ошибки (если есть)\n\n⏱ Ответ может занять некоторое время. Спасибо за понимание!",
                "message_sent": "📦 <b>Ваше сообщение отправлено в поддержку!</b>\n\nМы получили ваш запрос и скоро свяжемся с вами.\n\n⏱ Обычно мы отвечаем в течение нескольких часов.\n\nСпасибо за ожидание! 💙",
                "message_edited": (
                    "✏️ <b>Сообщение отредактировано только в вашем чате.</b>\n\nЧтобы отправить отредактированное сообщение, отправьте его как новое."
                ),
                "user_started_bot": (
                    f"Пользователь {hbold('{name}')} запустил бота!\n\n"
                    "Список доступных команд:\n\n"
                    "• /ban\n"
                    "Заблокировать/Разблокировать пользователя"
                    "<blockquote>Заблокируйте пользователя, если не хотите получать от него сообщения.</blockquote>\n\n"
                    "• /silent\n"
                    "Включить/Выключить тихий режим"
                    "<blockquote>Когда тихий режим включен, сообщения не отправляются пользователю.</blockquote>\n\n"
                    "• /information\n"
                    "Информация о пользователе"
                    "<blockquote>Получить сообщение с основной информацией о пользователе.</blockquote>"
                ),
                "user_restarted_bot": f"Пользователь {hbold('{name}')} перезапустил бота!",
                "user_stopped_bot": f"Пользователь {hbold('{name}')} остановил бота!",
                "user_blocked": "<b>Пользователь заблокирован!</b> Сообщения от пользователя не принимаются.",
                "user_unblocked": "<b>Пользователь разблокирован!</b> Сообщения от пользователя снова принимаются.",
                "blocked_by_user": "<b>Сообщение не отправлено!</b> Бот заблокирован пользователем.",
                "user_information": (
                    "<b>Краткая справка по командам:</b>\n\n"
                    "• <code>/ban</code> — блокировать или разблокировать пользователя.\n"
                    "• <code>/silent</code> — включить или выключить тихий режим.\n"
                    "• <code>/information</code> — показать эту краткую справку."
                ),
                "message_not_sent": "<b>Сообщение не отправлено!</b> Произошла непредвиденная ошибка.",
                "message_sent_to_user": "<b>Сообщение отправлено пользователю!</b>",
                "silent_mode_enabled": (
                    "<b>Тихий режим активирован!</b> Сообщения не будут доставляться пользователю."
                ),
                "silent_mode_disabled": (
                    "<b>Тихий режим деактивирован!</b> Пользователь будет получать все сообщения."
                )
            }
        }
