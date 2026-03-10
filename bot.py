import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import TOKEN
from database import init_crm_db
from modules.admin import router as admin_router
from modules.crm_fans import router as crm_router
from modules.categories import router as categories_router
from modules.stats_module import router as stats_router

logging.basicConfig(level=logging.INFO)


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")

    init_crm_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Убираем старый webhook и очередь
    await bot.delete_webhook(drop_pending_updates=True)

    # ВАЖНО: сначала admin + crm, потом categories
    dp.include_router(admin_router)
    dp.include_router(crm_router)
    dp.include_router(categories_router)
    dp.include_router(stats_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
