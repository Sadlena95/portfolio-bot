import asyncio
import logging
import os
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonCommands

from bot.handlers import router
from bot.utils.logging_config import setup_logging
from config import BOT_TOKEN, GOOGLE_APPLICATION_CREDENTIALS, TELEGRAM_PROXY

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Приветствие"),
        BotCommand(command="menu", description="Категории портфолио"),
    ]
    await bot.set_my_commands(commands)
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands(text="📂 Меню"))


async def health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def start_http_server() -> None:
    try:
        app = web.Application()
        app.router.add_get("/health", health)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 8300))
        host = '0.0.0.0'
        site = web.TCPSite(runner, host=host, port=port)
        await site.start()
        logger.info("HTTP health server started on :::%s", port)
        await asyncio.Event().wait()
    except Exception as exc:
        logger.exception("HTTP health server failed: %s", exc)


async def main() -> None:
    setup_logging()

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не задан. Добавьте токен в файл .env")
        sys.exit(1)

    if not GOOGLE_APPLICATION_CREDENTIALS:
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS не задан — категории портфолио не работают"
        )
    else:
        logger.info("Google Drive key: %s", GOOGLE_APPLICATION_CREDENTIALS)

    bot_kwargs = {
        "token": BOT_TOKEN,
        "default": DefaultBotProperties(parse_mode=ParseMode.HTML),
    }
    if TELEGRAM_PROXY:
        bot_kwargs["session"] = AiohttpSession(proxy=TELEGRAM_PROXY)
        logger.info("Используется прокси: %s", TELEGRAM_PROXY)

    dp = Dispatcher()
    dp.include_router(router)

    async with Bot(**bot_kwargs) as bot:
        try:
            me = await bot.get_me()
        except Exception as exc:
            logger.error(
                "Не удалось подключиться к api.telegram.org: %s\n"
                "MTProto в Telegram-клиенте работает только для приложения, "
                "не для Bot API. Добавьте в .env локальный HTTP/SOCKS-прокси:\n"
                "  TELEGRAM_PROXY=socks5://127.0.0.1:1080\n"
                "или включите системный VPN и перезапустите бота.",
                exc,
            )
            sys.exit(1)

        logger.info("Подключение успешно: @%s (id=%s)", me.username, me.id)
        await set_commands(bot)
        await asyncio.gather(
            start_http_server(),
            dp.start_polling(bot),
        )


if __name__ == "__main__":
    asyncio.run(main())
