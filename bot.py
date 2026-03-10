import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from config import TOKEN
from database import init_crm_db
from modules.admin import router as admin_router
from modules.crm_fans import router as crm_router
from modules.categories import router as categories_router
from modules.stats_module import router as stats_router

logging.basicConfig(level=logging.INFO)

# =========================
# Локальный UI-роутер
# =========================
ui_router = Router()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🏠 Старт"),
            KeyboardButton(text="📊 CRM"),
        ],
        [
            KeyboardButton(text="🔎 Найти фаната"),
            KeyboardButton(text="📈 Статистика"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери действие...",
)

START_TEXT = (
    "🤖 <b>Панель управления ботом</b>\n\n"
    "Доступно через кнопки:\n"
    "• 📊 CRM\n"
    "• 🔎 Найти фаната\n"
    "• 📈 Статистика\n\n"
    "Основные команды:\n"
    "• /crm — открыть CRM\n"
    "• /fan @u123456789 — найти фаната\n"
    "• /start — открыть это меню"
)


@ui_router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        START_TEXT,
        reply_markup=main_menu,
        parse_mode="HTML",
    )


@ui_router.message(F.text == "🏠 Старт")
async def btn_start(message: Message):
    await message.answer(
        START_TEXT,
        reply_markup=main_menu,
        parse_mode="HTML",
    )


@ui_router.message(F.text == "📊 CRM")
async def btn_crm(message: Message):
    # Не дублируем логику crm_router, просто подсказываем команду
    await message.answer(
        "📊 <b>CRM</b>\n\n"
        "Открой CRM командой:\n"
        "<code>/crm</code>",
        parse_mode="HTML",
    )


@ui_router.message(F.text == "🔎 Найти фаната")
async def btn_find_fan(message: Message):
    await message.answer(
        "🔎 <b>Поиск фаната</b>\n\n"
        "Отправь команду в таком виде:\n"
        "<code>/fan @u123456789</code>\n\n"
        "Пример:\n"
        "<code>/fan @u520088948</code>",
        parse_mode="HTML",
    )


@ui_router.message(F.text == "📈 Статистика")
async def btn_stats(message: Message):
    await message.answer(
        "📈 <b>Статистика</b>\n\n"
        "Используй команды из модуля статистики.\n"
        "Если хочешь, следующим сообщением я помогу красиво оформить и эту кнопку под твой текущий stats-модуль.",
        parse_mode="HTML",
    )


async def set_main_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Открыть главное меню"),
        BotCommand(command="crm", description="Открыть CRM"),
        BotCommand(command="fan", description="Найти фаната по ID"),
    ]
    await bot.set_my_commands(commands)


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")

    init_crm_db()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Убираем старый webhook и очередь
    await bot.delete_webhook(drop_pending_updates=True)

    # Команды в меню Telegram
    await set_main_commands(bot)

    # Сначала UI
    dp.include_router(ui_router)

    # Потом твои рабочие роутеры
    dp.include_router(admin_router)
    dp.include_router(crm_router)
    dp.include_router(categories_router)
    dp.include_router(stats_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
