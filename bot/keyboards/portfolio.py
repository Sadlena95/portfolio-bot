from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CATEGORIES: dict[str, str] = {
    "infographic": "Инфографика",
    "neurophoto": "Нейрофото",
    "video": "Видео",
}

MENU_MESSAGE = "Выберите категорию портфолио:"


def portfolio_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"portfolio:{key}")]
        for key, name in CATEGORIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
