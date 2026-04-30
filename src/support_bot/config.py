from dataclasses import dataclass
from typing import List

from environs import Env


@dataclass
class BotConfig:
    """
    Data class representing the configuration for the bot.

    Attributes:
    - TOKEN (str): The bot token.
    - DEV_IDS (list[int]): Admin user IDs.
    - GROUP_ID (int): The group chat ID.
    - BOT_EMOJI_ID (str): The custom emoji ID for the group's topic.
    """
    TOKEN: str
    DEV_IDS: List[int]
    GROUP_ID: int
    BOT_EMOJI_ID: str


@dataclass
class RedisConfig:
    """
    Data class representing the configuration for Redis.

    Attributes:
    - HOST (str): The Redis host.
    - PORT (int): The Redis port.
    - DB (int): The Redis database number.
    """
    HOST: str
    PORT: int
    DB: int
    PASSWORD: str

    def dsn(self) -> str:
        """
        Generates a Redis connection DSN (Data Source Name) using the provided host, port, and database.

        :return: The generated DSN.
        """
        if self.PASSWORD:
            return f"redis://:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"


@dataclass
class Config:
    """
    Data class representing the overall configuration for the application.

    Attributes:
    - bot (BotConfig): The bot configuration.
    - redis (RedisConfig): The Redis configuration.
    """
    bot: BotConfig
    redis: RedisConfig


def _resolve_support_admin_ids(env: Env) -> List[int]:
    admin_ids_raw = env.str("ADMIN_IDS", "").strip()
    if not admin_ids_raw:
        raise ValueError(
            "ADMIN_IDS is empty. Set ADMIN_IDS with at least one admin ID."
        )
    ids: List[int] = []
    for raw in admin_ids_raw.split(","):
        value = raw.strip()
        if not value:
            continue
        ids.append(int(value))
    if not ids:
        raise ValueError("ADMIN_IDS has invalid format.")
    return ids


def load_config() -> Config:
    """
    Load the configuration from environment variables and return a Config object.

    :return: The Config object with loaded configuration.
    """
    env = Env()
    env.read_env()

    return Config(
        bot=BotConfig(
            TOKEN=env.str("SUPPORT_BOT_TOKEN"),
            DEV_IDS=_resolve_support_admin_ids(env),
            GROUP_ID=env.int("SUPPORT_BOT_GROUP_ID"),
            BOT_EMOJI_ID=env.str("SUPPORT_BOT_EMOJI_ID"),
        ),
        redis=RedisConfig(
            HOST=env.str("SUPPORT_BOT_REDIS_HOST", env.str("REDIS_HOST", "localhost")),
            PORT=env.int("SUPPORT_BOT_REDIS_PORT", env.int("REDIS_PORT", 6379)),
            DB=env.int("SUPPORT_BOT_REDIS_DB", 1),
            PASSWORD=env.str("SUPPORT_BOT_REDIS_PASSWORD", env.str("REDIS_PASSWORD", "")),
        ),
    )
