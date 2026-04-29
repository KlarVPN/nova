import secrets
from pathlib import Path
import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)

_WORDS_PATH = Path(__file__).parents[4] / "assets" / "words_ru5.txt"
_words: list[str] = []


def _load_words() -> list[str]:
    global _words
    if not _words:
        _words = [w.strip() for w in _WORDS_PATH.read_text(encoding="utf-8").splitlines() if w.strip()]
    return _words


def generate_key() -> str:
    words = _load_words()
    chosen = secrets.SystemRandom().sample(words, 6)
    return "-".join(chosen)


def hash_key(key: str) -> str:
    return _ph.hash(_normalize(key))


def verify_key(key: str, stored_hash: str) -> bool:
    try:
        return _ph.verify(stored_hash, _normalize(key))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _normalize(key: str) -> str:
    normalized = re.sub(r"[-\s]+", " ", key.lower()).strip()
    return " ".join(normalized.split())
