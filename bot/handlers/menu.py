import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.handlers.portfolio_page import send_portfolio_page
from bot.keyboards.portfolio import CATEGORIES, MENU_MESSAGE, portfolio_keyboard
from bot.services.drive_client import DriveUnavailableError, get_files_from_folder
from bot.services.portfolio_cache import set_category_files

logger = logging.getLogger(__name__)

router = Router()

DRIVE_UNAVAILABLE_MESSAGE = "Сервис временно недоступен. Попробуйте позже."


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    logger.info("Команда /menu от user_id=%s", message.from_user.id if message.from_user else "?")
    await message.answer(MENU_MESSAGE, reply_markup=portfolio_keyboard())


@router.callback_query(F.data.startswith("portfolio:"))
async def on_category_selected(callback: CallbackQuery) -> None:
    category_key = callback.data.removeprefix("portfolio:")
    category_name = CATEGORIES.get(category_key)

    if not category_name:
        await callback.answer("Неизвестная категория", show_alert=True)
        return

    user_id = callback.from_user.id if callback.from_user else 0
    logger.info("Категория %s от user_id=%s", category_name, user_id)
    await callback.answer()

    try:
        files = await get_files_from_folder(category_name)
    except DriveUnavailableError as exc:
        logger.error("Google Drive unavailable for category=%s: %s", category_name, exc)
        if callback.message:
            await callback.message.answer(DRIVE_UNAVAILABLE_MESSAGE)
        return

    set_category_files(user_id, category_key, category_name, files)

    if callback.message:
        await send_portfolio_page(callback.message, user_id, category_key, page=0)
