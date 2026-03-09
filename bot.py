import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import TOKEN
from modules.admin import router as admin_router
from modules.categories import router as categories_router
from modules.crm_fans import router as crm_router
from modules.stats_module import router as stats_router


logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)

    dp.include_router(admin_router)
    dp.include_router(categories_router)
    dp.include_router(crm_router)
    dp.include_router(stats_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
