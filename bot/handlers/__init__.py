from aiogram import Router

from bot.handlers.menu import router as menu_router
from bot.handlers.portfolio_callbacks import router as portfolio_callbacks_router
from bot.handlers.start import router as start_router

router = Router()
router.include_router(start_router)
router.include_router(menu_router)
router.include_router(portfolio_callbacks_router)

__all__ = ["router"]
