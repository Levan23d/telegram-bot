import asyncio
import json
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 493688036

DATA_FILE = "buttons.json"
STATS_FILE = "stats.json"
CRM_DB = "fans_crm.db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_category = {}
user_state = {}
temp_data = {}

# =========================
# LOAD DATA
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {"categories": {}}
        save_data(data)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_stats():
    if not os.path.exists(STATS_FILE):
        data = {
            "users": {},
            "total_starts": 0,
            "category_clicks": {}
        }
        save_stats(data)
        return data

    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data_store = load_data()
stats_store = load_stats()

# =========================
# CRM DATABASE
# =========================

def init_crm_db():

    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        model_name TEXT,
        interests TEXT,
        total_spent REAL DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fan_id INTEGER,
        item_name TEXT,
        amount REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def add_fan_db(username, model_name, interests, notes):

    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO fans (username,model_name,interests,notes) VALUES (?,?,?,?)",
        (username, model_name, interests, notes)
    )

    conn.commit()

    fan_id = cur.lastrowid
    conn.close()

    return fan_id

def add_purchase_db(fan_id, item_name, amount):

    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO purchases (fan_id,item_name,amount) VALUES (?,?,?)",
        (fan_id, item_name, amount)
    )

    cur.execute(
        "UPDATE fans SET total_spent = total_spent + ? WHERE id = ?",
        (amount, fan_id)
    )

    conn.commit()
    conn.close()

def get_fan_by_id(fan_id):

    conn = sqlite3.connect(CRM_DB)
    cur = conn.cursor()

    cur.execute("SELECT * FROM fans WHERE id=?", (fan_id,))
    row = cur.fetchone()

    conn.close()
    return row

# =========================
# MENUS
# =========================

def build_main_menu(user_id):

    rows = []

    for category in data_store["categories"]:
        rows.append([KeyboardButton(text=category)])

    rows.append([KeyboardButton(text="👤 Фанаты")])

    if user_id == ADMIN_ID:

        rows.append([KeyboardButton(text="➕ Категория")])
        rows.append([KeyboardButton(text="➕ Текст")])
        rows.append([KeyboardButton(text=" Статистика")])
        rows.append([KeyboardButton(text=" Пользователи")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def build_fans_menu():

    rows = [
        [KeyboardButton(text="➕ Добавить фаната")],
        [KeyboardButton(text="💸 Добавить покупку")],
        [KeyboardButton(text="🔎 Найти фаната")],
        [KeyboardButton(text="⬅ Назад")]
    ]

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

# =========================
# START
# =========================

@dp.message(F.text == "/start")
async def start(message: Message):

    user_id = str(message.from_user.id)

    if user_id not in stats_store["users"]:
        stats_store["users"][user_id] = {"starts": 1}
    else:
        stats_store["users"][user_id]["starts"] += 1

    stats_store["total_starts"] += 1

    save_stats(stats_store)

    await message.answer(
        "Главное меню",
        reply_markup=build_main_menu(message.from_user.id)
    )

# =========================
# CRM MENU
# =========================

@dp.message(F.text == "👤 Фанаты")
async def fans_menu(message: Message):

    await message.answer(
        "CRM фанатов",
        reply_markup=build_fans_menu()
    )

# =========================
# ADD FAN
# =========================

@dp.message(F.text == "➕ Добавить фаната")
async def add_fan_start(message: Message):

    user_state[message.from_user.id] = "fan_username"

    await message.answer("Username фаната")

@dp.message()
async def universal_handler(message: Message):

    user_id = message.from_user.id
    state = user_state.get(user_id)

    if state == "fan_username":

        temp_data[user_id] = {"username": message.text}

        user_state[user_id] = "fan_model"

        await message.answer("Модель")
        return

    if state == "fan_model":

        temp_data[user_id]["model"] = message.text

        user_state[user_id] = "fan_interests"

        await message.answer("Интересы")
        return

    if state == "fan_interests":

        temp_data[user_id]["interests"] = message.text

        user_state[user_id] = "fan_notes"

        await message.answer("Заметка")
        return

    if state == "fan_notes":

        data = temp_data[user_id]

        fan_id = add_fan_db(
            data["username"],
            data["model"],
            data["interests"],
            message.text
        )

        user_state.pop(user_id)
        temp_data.pop(user_id)

        await message.answer(f"Фанат добавлен ID {fan_id}")
        return

# =========================
# MAIN
# =========================

async def main():

    init_crm_db()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
