import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router()


def _build_start_message(username: str | None) -> str:
    greeting = f"Привет, {username}!" if username else "Привет!"
    return (
        f"👋 {greeting} Я - твой гид по портфолио дизайнера-нейрокреатора Елены Садофьевой.\n\n"
        "Я здесь, чтобы познакомить тебя с её работами - от стильной инфографики "
        "до атмосферных нейрофото и видео.\n\n"
        "Рад, что ты здесь! 😊\n\n"
        "Чтобы посмотреть работы, нажми на кнопку «📂 Меню» внизу экрана "
        "или отправь команду /menu.\n\n"
        "Выбери то, что тебе интересно, и наслаждайся!"
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    logger.info("Команда /start от user_id=%s", message.from_user.id if message.from_user else "?")
    username = message.from_user.username if message.from_user else None
    await message.answer(_build_start_message(username))
