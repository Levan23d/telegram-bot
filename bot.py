import asyncio
import json
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8700901073:AAEjGyxRxtX43OntdRBaRLmeOMgnb7rdfxg"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "data.json"

CATEGORIES = [
    "🍑 ANAL",
    "🍆 DILDO",
    "💬 SEXTING",
    "🎥 VIDEOCALL",
    "⭐ DICK RATE",
    "✋ FINGERS",
]

# Память текущего состояния пользователя
user_category = {}
user_mode = {}

# ---------- Работа с файлом ----------

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {}
        for cat in CATEGORIES:
            data[cat] = {
                "send": "Здесь пока нет рассылки",
                "desc": "Здесь пока нет описания"
            }
        save_data(data)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data_store = load_data()

# ---------- Клавиатуры ----------

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍑 ANAL"), KeyboardButton(text="🍆 DILDO")],
        [KeyboardButton(text="💬 SEXTING"), KeyboardButton(text="🎥 VIDEOCALL")],
        [KeyboardButton(text="⭐ DICK RATE"), KeyboardButton(text="✋ FINGERS")],
    ],
    resize_keyboard=True
)

submenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📨 Рассылка"), KeyboardButton(text="📄 Описание")],
        [KeyboardButton(text="➕ Добавить рассылку"), KeyboardButton(text="➕ Добавить описание")],
        [KeyboardButton(text="⬅ Назад")],
    ],
    resize_keyboard=True
)

# ---------- Команды ----------

@dp.message(F.text == "/start")
async def start_handler(message: Message):
    user_mode.pop(message.from_user.id, None)
    await message.answer("Выбери категорию", reply_markup=menu)


@dp.message(F.text.in_(CATEGORIES))
async def category_handler(message: Message):
    user_category[message.from_user.id] = message.text
    user_mode.pop(message.from_user.id, None)
    await message.answer(f"Категория: {message.text}\nВыбери действие", reply_markup=submenu)


@dp.message(F.text == "📨 Рассылка")
async def show_send_handler(message: Message):
    cat = user_category.get(message.from_user.id)
    if not cat:
        await message.answer("Сначала выбери категорию", reply_markup=menu)
        return

    await message.answer(data_store[cat]["send"])


@dp.message(F.text == "📄 Описание")
async def show_desc_handler(message: Message):
    cat = user_category.get(message.from_user.id)
    if not cat:
        await message.answer("Сначала выбери категорию", reply_markup=menu)
        return

    await message.answer(data_store[cat]["desc"])


@dp.message(F.text == "➕ Добавить рассылку")
async def add_send_handler(message: Message):
    cat = user_category.get(message.from_user.id)
    if not cat:
        await message.answer("Сначала выбери категорию", reply_markup=menu)
        return

    user_mode[message.from_user.id] = "add_send"
    await message.answer(f"Отправь новый текст рассылки для {cat}")


@dp.message(F.text == "➕ Добавить описание")
async def add_desc_handler(message: Message):
    cat = user_category.get(message.from_user.id)
    if not cat:
        await message.answer("Сначала выбери категорию", reply_markup=menu)
        return

    user_mode[message.from_user.id] = "add_desc"
    await message.answer(f"Отправь новое описание для {cat}")


@dp.message(F.text == "⬅ Назад")
async def back_handler(message: Message):
    user_mode.pop(message.from_user.id, None)
    await message.answer("Главное меню", reply_markup=menu)


@dp.message()
async def text_input_handler(message: Message):
    user_id = message.from_user.id
    mode = user_mode.get(user_id)
    cat = user_category.get(user_id)

    if not mode:
        await message.answer("Выбери категорию или действие с кнопок")
        return

    if not cat:
        await message.answer("Сначала выбери категорию", reply_markup=menu)
        user_mode.pop(user_id, None)
        return

    text = message.text.strip()

    if mode == "add_send":
        data_store[cat]["send"] = text
        save_data(data_store)
        user_mode.pop(user_id, None)
        await message.answer(f"Рассылка для {cat} сохранена ✅", reply_markup=submenu)
        return

    if mode == "add_desc":
        data_store[cat]["desc"] = text
        save_data(data_store)
        user_mode.pop(user_id, None)
        await message.answer(f"Описание для {cat} сохранено ✅", reply_markup=submenu)
        return


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())