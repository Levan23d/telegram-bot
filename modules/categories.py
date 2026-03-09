from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.event.bases import SkipHandler

from config import ADMIN_ID
from state import data_store, stats_store, save_stats, user_category, user_state, temp_data

router = Router()


def build_main_menu(user_id):
    rows = []

    for category in data_store["categories"]:
        rows.append([KeyboardButton(text=category)])

    rows.append([KeyboardButton(text="👤 Фанаты")])

    if user_id == ADMIN_ID:
        rows.append([KeyboardButton(text="➕ Категория")])
        rows.append([KeyboardButton(text="➕ Текст")])
        rows.append([KeyboardButton(text="Статистика")])
        rows.append([KeyboardButton(text="Пользователи")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = str(message.from_user.id)

    if user_id not in stats_store["users"]:
        stats_store["users"][user_id] = {"starts": 1}
    else:
        stats_store["users"][user_id]["starts"] += 1

    stats_store["total_starts"] += 1
    save_stats(stats_store)

    user_state.pop(message.from_user.id, None)
    temp_data.pop(message.from_user.id, None)
    user_category.pop(message.from_user.id, None)

    await message.answer(
        "Главное меню",
        reply_markup=build_main_menu(message.from_user.id)
    )


@router.message()
async def category_handler(message: Message):
    text = message.text
    user_id = message.from_user.id

    if text in data_store["categories"]:
        user_category[user_id] = text

        stats_store["category_clicks"][text] = stats_store["category_clicks"].get(text, 0) + 1
        save_stats(stats_store)

        buttons = []

        for item in data_store["categories"][text]:
            buttons.append([KeyboardButton(text=item)])

        buttons.append([KeyboardButton(text="⬅ Назад")])

        await message.answer(
            f"Категория: {text}",
            reply_markup=ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        )
        return

    elif text == "⬅ Назад":
        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)
        user_category.pop(user_id, None)

        await message.answer(
            "Главное меню",
            reply_markup=build_main_menu(user_id)
        )
        return

    elif user_id in user_category:
        category = user_category[user_id]

        if text in data_store["categories"][category]:
            await message.answer(
                data_store["categories"][category][text]
            )
            return

    raise SkipHandler()
