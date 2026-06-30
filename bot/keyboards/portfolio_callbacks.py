import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.handlers.portfolio_page import send_portfolio_page
from bot.keyboards.pagination import PortfolioCallback
from bot.keyboards.portfolio import MENU_MESSAGE, portfolio_keyboard
from bot.services.portfolio_cache import get_session

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(PortfolioCallback.filter(F.action == "noop"))
async def on_pagination_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(PortfolioCallback.filter(F.action == "page"))
async def on_page_change(callback: CallbackQuery, callback_data: PortfolioCallback) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    session = get_session(user_id)

    if not session or session.get("category_key") != callback_data.category:
        await callback.answer("Список устарел. Выберите категорию заново.", show_alert=True)
        return

    logger.info(
        "Page change user_id=%s category=%s page=%s",
        user_id,
        callback_data.category,
        callback_data.page,
    )
    await callback.answer()

    if callback.message:
        await send_portfolio_page(
            callback.message,
            user_id,
            callback_data.category,
            callback_data.page,
        )


@router.callback_query(PortfolioCallback.filter(F.action == "categories"))
async def on_back_to_categories(callback: CallbackQuery) -> None:
    logger.info(
        "Back to categories user_id=%s",
        callback.from_user.id if callback.from_user else 0,
    )
    await callback.answer()

    if callback.message:
        await callback.message.answer(MENU_MESSAGE, reply_markup=portfolio_keyboard())
