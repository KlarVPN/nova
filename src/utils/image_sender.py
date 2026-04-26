import logging
from pathlib import Path

from aiogram import types
from aiogram.types import FSInputFile, InputMediaPhoto

IMAGES_DIR = Path(__file__).parent.parent.parent / "assets" / "images"


async def answer_with_image(
    target: types.Message,
    image_name: str,
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
) -> None:
    image_path = IMAGES_DIR / image_name
    if not image_path.exists():
        logging.warning("Image not found: %s, falling back to text", image_path)
        await target.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return

    await target.answer_photo(
        photo=FSInputFile(image_path),
        caption=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


async def edit_with_image(
    target: types.Message,
    image_name: str,
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
) -> None:
    image_path = IMAGES_DIR / image_name
    if not image_path.exists():
        logging.warning("Image not found: %s, falling back to text", image_path)
        try:
            await target.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            await target.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return

    try:
        await target.edit_media(
            media=InputMediaPhoto(media=FSInputFile(image_path), caption=text, parse_mode=parse_mode),
            reply_markup=reply_markup,
        )
    except Exception:
        await target.answer_photo(
            photo=FSInputFile(image_path),
            caption=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
