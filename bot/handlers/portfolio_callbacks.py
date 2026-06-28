import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.handlers.portfolio_page import send_file_view, send_portfolio_page
from bot.keyboards.pagination import PortfolioCallback
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


@router.callback_query(PortfolioCallback.filter(F.action == "view_file"))
async def on_view_file(callback: CallbackQuery, callback_data: PortfolioCallback) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    session = get_session(user_id)

    if not session or session.get("category_key") != callback_data.category:
        await callback.answer("Список устарел. Выберите категорию заново.", show_alert=True)
        return

    logger.info(
        "View file user_id=%s category=%s page=%s file_idx=%s",
        user_id,
        callback_data.category,
        callback_data.page,
        callback_data.file_idx,
    )
    await callback.answer()

    if callback.message:
        await send_file_view(
            callback.message,
            user_id,
            callback_data.category,
            callback_data.page,
            callback_data.file_idx,
        )


@router.callback_query(PortfolioCallback.filter(F.action == "back_to_list"))
async def on_back_to_list(callback: CallbackQuery, callback_data: PortfolioCallback) -> None:
    user_id = callback.from_user.id if callback.from_user else 0
    session = get_session(user_id)

    if not session or session.get("category_key") != callback_data.category:
        await callback.answer("Список устарел. Выберите категорию заново.", show_alert=True)
        return

    logger.info(
        "Back to list user_id=%s category=%s page=%s",
        user_id,
        callback_data.category,
        callback_data.page,
    )
    await callback.answer()

    if callback.message:
        try:
            await callback.message.delete()
        except Exception as exc:
            logger.warning("Could not delete view message: %s", exc)

        await send_portfolio_page(
            callback.message,
            user_id,
            callback_data.category,
            callback_data.page,
        )
