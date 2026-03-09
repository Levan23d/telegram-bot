import asyncio
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 493688036
DATA_FILE = "buttons.json"
STATS_FILE = "stats.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_category = {}
user_state = {}
temp_data = {}


def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "categories": {
                "🍆 DILDO": {
                    "_description": "Тексты и рассылки с дилдо",
                    "Рассылка 1": "Текст для DILDO 1",
                    "Рассылка 2": "Текст для DILDO 2"
                },
                "🍑 ANAL": {
                    "_description": "Тексты и рассылки с анальным фокусом",
                    "Рассылка 1": "Текст для ANAL 1"
                }
            }
        }
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


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def get_category_description(category_name: str) -> str:
    category = data_store["categories"].get(category_name, {})
    return category.get("_description", "Выбери текст 👇")


def get_category_items(category_name: str) -> dict:
    category = data_store["categories"].get(category_name, {})
    return {k: v for k, v in category.items() if k != "_description"}


def build_main_menu(user_id: int):
    categories = list(data_store["categories"].keys())

    rows = []
    row = []

    for category in categories:
        row.append(KeyboardButton(text=category))
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    if is_admin(user_id):
        rows.append([KeyboardButton(text="➕ Категория"), KeyboardButton(text="➕ Текст")])
        rows.append([KeyboardButton(text="✏️ Изменить"), KeyboardButton(text="🗑 Удалить текст")])
        rows.append([KeyboardButton(text="🗑 Удалить категорию"), KeyboardButton(text="✏️ Описание")])
        rows.append([KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👤 Пользователи")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def build_category_menu(category_name: str):
    items = get_category_items(category_name)

    rows = []
    for item_name in items.keys():
        rows.append([KeyboardButton(text=item_name)])

    rows.append([KeyboardButton(text="⬅ Назад")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@dp.message(F.text == "/start")
async def start_handler(message: Message):
    user = message.from_user
    user_id = str(user.id)

    if user_id not in stats_store["users"]:
        stats_store["users"][user_id] = {
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "starts": 1
        }

        if user.id != ADMIN_ID:
            await bot.send_message(
                ADMIN_ID,
                f"👤 Новый пользователь\n\n"
                f"ID: {user.id}\n"
                f"Username: @{user.username if user.username else 'нет'}\n"
                f"Имя: {user.first_name or '—'}\n"
                f"Фамилия: {user.last_name or '—'}"
            )
    else:
        stats_store["users"][user_id]["username"] = user.username or ""
        stats_store["users"][user_id]["first_name"] = user.first_name or ""
        stats_store["users"][user_id]["last_name"] = user.last_name or ""
        stats_store["users"][user_id]["starts"] += 1

    stats_store["total_starts"] += 1
    save_stats(stats_store)

    user_category.pop(user.id, None)
    user_state.pop(user.id, None)
    temp_data.pop(user.id, None)

    await message.answer(
        "Привет 👋\n\n"
        "Это библиотека рассылок, описаний видео и готовых сообщений.\n\n"
        "Выбери нужную категорию ниже 👇",
        reply_markup=build_main_menu(user.id)
    )


@dp.message(F.text == "/stats")
@dp.message(F.text == "📊 Статистика")
async def stats_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    total_users = len(stats_store["users"])
    total_starts = stats_store["total_starts"]

    if stats_store["category_clicks"]:
        top_category = max(stats_store["category_clicks"], key=stats_store["category_clicks"].get)
        top_count = stats_store["category_clicks"][top_category]
    else:
        top_category = "—"
        top_count = 0

    await message.answer(
        f"📊 Статистика\n\n"
        f"Пользователей: {total_users}\n"
        f"Всего запусков /start: {total_starts}\n"
        f"Популярная категория: {top_category} ({top_count})"
    )


@dp.message(F.text == "/users")
@dp.message(F.text == "👤 Пользователи")
async def users_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not stats_store["users"]:
        await message.answer("Пользователей пока нет")
        return

    lines = []
    for uid, info in list(stats_store["users"].items())[:30]:
        username = f"@{info['username']}" if info["username"] else "—"
        first_name = info["first_name"] or "—"
        starts = info["starts"]

        lines.append(
            f"{first_name} | {username}\n"
            f"ID: {uid} | Starts: {starts}"
        )

    text = "👤 Пользователи:\n\n" + "\n\n".join(lines)
    await message.answer(text)


@dp.message(F.text == "⬅ Назад")
async def back_handler(message: Message):
    user_category.pop(message.from_user.id, None)
    user_state.pop(message.from_user.id, None)
    temp_data.pop(message.from_user.id, None)

    await message.answer(
        "Главное меню",
        reply_markup=build_main_menu(message.from_user.id)
    )


@dp.message(F.text == "➕ Категория")
async def add_category_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_new_category_name"
    await message.answer("Отправь название новой категории")


@dp.message(F.text == "➕ Текст")
async def add_text_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_category_for_new_text"
    await message.answer("Отправь точное название категории, куда добавить текст")


@dp.message(F.text == "✏️ Изменить")
async def edit_text_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_category_for_edit"
    await message.answer("Отправь точное название категории, где находится текст")


@dp.message(F.text == "🗑 Удалить текст")
async def delete_text_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_category_for_delete_text"
    await message.answer("Отправь точное название категории, где находится текст")


@dp.message(F.text == "🗑 Удалить категорию")
async def delete_category_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_category_to_delete"
    await message.answer("Отправь точное название категории, которую нужно удалить")


@dp.message(F.text == "✏️ Описание")
async def edit_description_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_category_for_description"
    await message.answer("Отправь точное название категории, у которой нужно изменить описание")


@dp.message()
async def universal_handler(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if text in data_store["categories"] and not state:
        user_category[user_id] = text

        stats_store["category_clicks"][text] = stats_store["category_clicks"].get(text, 0) + 1
        save_stats(stats_store)

        description = get_category_description(text)
        await message.answer(
            f"Категория: {text}\n\n{description}",
            reply_markup=build_category_menu(text)
        )
        return

    current_category = user_category.get(user_id)
    if current_category and not state:
        category_items = get_category_items(current_category)
        if text in category_items:
            await message.answer(category_items[text])
            return

    if state == "waiting_new_category_name":
        if text in data_store["categories"]:
            await message.answer("Такая категория уже есть")
            return

        data_store["categories"][text] = {
            "_description": "Описание категории"
        }
        save_data(data_store)

        user_state.pop(user_id, None)
        await message.answer(
            f"Категория {text} добавлена ✅",
            reply_markup=build_main_menu(user_id)
        )
        return

    if state == "waiting_category_for_new_text":
        if text not in data_store["categories"]:
            await message.answer("Такой категории нет")
            return

        temp_data[user_id] = {"category": text}
        user_state[user_id] = "waiting_new_text_button_name"
        await message.answer("Отправь название кнопки текста")
        return

    if state == "waiting_new_text_button_name":
        temp_data[user_id]["button_name"] = text
        user_state[user_id] = "waiting_new_text_value"
        await message.answer("Теперь отправь сам текст")
        return

    if state == "waiting_new_text_value":
        category = temp_data[user_id]["category"]
        button_name = temp_data[user_id]["button_name"]

        data_store["categories"][category][button_name] = text
        save_data(data_store)

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer(
            f"Текст {button_name} добавлен в {category} ✅",
            reply_markup=build_main_menu(user_id)
        )
        return

    if state == "waiting_category_for_edit":
        if text not in data_store["categories"]:
            await message.answer("Такой категории нет")
            return

        temp_data[user_id] = {"category": text}
        user_state[user_id] = "waiting_text_button_for_edit"
        await message.answer("Отправь название текста, который нужно изменить")
        return

    if state == "waiting_text_button_for_edit":
        category = temp_data[user_id]["category"]
        category_items = get_category_items(category)
        if text not in category_items:
            await message.answer("Такого текста нет в этой категории")
            return

        temp_data[user_id]["button_name"] = text
        user_state[user_id] = "waiting_new_value_for_edit"
        await message.answer("Отправь новый текст")
        return

    if state == "waiting_new_value_for_edit":
        category = temp_data[user_id]["category"]
        button_name = temp_data[user_id]["button_name"]

        data_store["categories"][category][button_name] = text
        save_data(data_store)

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer(
            f"Текст {button_name} обновлён ✅",
            reply_markup=build_main_menu(user_id)
        )
        return

    if state == "waiting_category_for_delete_text":
        if text not in data_store["categories"]:
            await message.answer("Такой категории нет")
            return

        temp_data[user_id] = {"category": text}
        user_state[user_id] = "waiting_text_button_to_delete"
        await message.answer("Отправь название текста, который нужно удалить")
        return

    if state == "waiting_text_button_to_delete":
        category = temp_data[user_id]["category"]
        category_items = get_category_items(category)
        if text not in category_items:
            await message.answer("Такого текста нет в этой категории")
            return

        del data_store["categories"][category][text]
        save_data(data_store)

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer(
            f"Текст {text} удалён ✅",
            reply_markup=build_main_menu(user_id)
        )
        return

    if state == "waiting_category_to_delete":
        if text not in data_store["categories"]:
            await message.answer("Такой категории нет")
            return

        del data_store["categories"][text]
        save_data(data_store)

        user_state.pop(user_id, None)

        await message.answer(
            f"Категория {text} удалена ✅",
            reply_markup=build_main_menu(user_id)
        )
        return

    if state == "waiting_category_for_description":
        if text not in data_store["categories"]:
            await message.answer("Такой категории нет")
            return

        temp_data[user_id] = {"category": text}
        user_state[user_id] = "waiting_new_description"
        await message.answer("Отправь новое описание категории")
        return

    if state == "waiting_new_description":
        category = temp_data[user_id]["category"]
        data_store["categories"][category]["_description"] = text
        save_data(data_store)

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer(
            f"Описание для {category} обновлено ✅",
            reply_markup=build_main_menu(user_id)
        )
        return

    await message.answer(
        "Нажми кнопку из меню",
        reply_markup=build_main_menu(user_id)
    )


async def main():
    if not TOKEN:
        raise ValueError("Переменная BOT_TOKEN не задана")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
