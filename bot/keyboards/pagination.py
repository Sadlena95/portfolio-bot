from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

PAGE_SIZE = 5
MAX_VIDEO_BYTES = 50 * 1024 * 1024


class PortfolioCallback(CallbackData, prefix="pf"):
    """Компактный callback (лимит Telegram — 64 байта). file_idx — индекс в кэше."""

    action: str
    category: str
    page: int
    file_idx: int = 0


def _truncate_label(text: str, max_len: int = 28) -> str:
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 1]}…"


def pagination_keyboard(
    category_key: str,
    page: int,
    total_pages: int,
    total_files: int,
) -> InlineKeyboardMarkup | None:
    if total_files <= PAGE_SIZE:
        return None

    row: list[InlineKeyboardButton] = []
    if page > 0:
        row.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=PortfolioCallback(
                    action="page",
                    category=category_key,
                    page=page - 1,
                ).pack(),
            )
        )

    row.append(
        InlineKeyboardButton(
            text=f"📊 Страница {page + 1}/{total_pages}",
            callback_data=PortfolioCallback(
                action="noop",
                category=category_key,
                page=page,
            ).pack(),
        )
    )

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


def view_file_keyboard(
    category_key: str,
    page: int,
    file_idx: int,
    file_name: str,
    mime_type: str,
) -> InlineKeyboardMarkup:
    short_name = _truncate_label(file_name)
    if mime_type.startswith("video/"):
        label = f"🎬 Смотреть {short_name}"
    elif mime_type.startswith("image/"):
        label = f"👁️ Открыть {short_name}"
    else:
        label = f"📄 Открыть {short_name}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=PortfolioCallback(
                        action="view_file",
                        category=category_key,
                        page=page,
                        file_idx=file_idx,
                    ).pack(),
                )
            ]
        ]
    )


def back_to_list_keyboard(category_key: str, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к списку",
                    callback_data=PortfolioCallback(
                        action="back_to_list",
                        category=category_key,
                        page=page,
                    ).pack(),
                )
            ]
        ]
    )
