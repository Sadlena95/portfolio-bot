from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PAGE_SIZE = 5
MAX_VIDEO_BYTES = 50 * 1024 * 1024


class PortfolioCallback(CallbackData, prefix="pf"):
    """Компактный callback (лимит Telegram — 64 байта)."""

    action: str
    category: str
    page: int
    file_idx: int = 0


def pagination_keyboard(
    category_key: str,
    page: int,
    total_pages: int,
    total_files: int,
) -> InlineKeyboardMarkup | None:
    if total_files == 0:
        return None

    row: list[InlineKeyboardButton] = [
        InlineKeyboardButton(
            text="📂 Категории",
            callback_data=PortfolioCallback(
                action="categories",
                category=category_key,
                page=page,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data=PortfolioCallback(
                action="noop",
                category=category_key,
                page=page,
            ).pack(),
        ),
    ]

    if page < total_pages - 1:
        row.append(
            InlineKeyboardButton(
                text="➡️ Вперёд",
                callback_data=PortfolioCallback(
                    action="page",
                    category=category_key,
                    page=page + 1,
                ).pack(),
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[row])

