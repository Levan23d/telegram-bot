import asyncio
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 493688036
DATA_FILE = "buttons.json"

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
                    "Рассылка 1": "Текст для DILDO 1",
                    "Рассылка 2": "Текст для DILDO 2"
                },
                "🍑 ANAL": {
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


data_store = load_data()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


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
        rows.append([KeyboardButton(text="🗑 Удалить категорию")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def build_category_menu(category_name: str):
    items = data_store["categories"].get(category_name, {})

    rows = []
    for item_name in items.keys():
        rows.append([KeyboardButton(text=item_name)])

    rows.append([KeyboardButton(text="⬅ Назад")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@dp.message(F.text == "/start")
async def start_handler(message: Message):

    user = message.from_user

    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name

    # уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"👤 Новый пользователь\n\n"
        f"ID: {user_id}\n"
        f"Username: @{username}\n"
        f"Имя: {first_name}\n"
        f"Фамилия: {last_name}"
    )

    user_category.pop(user_id, None)
    user_state.pop(user_id, None)
    temp_data.pop(user_id, None)

    await message.answer(
        "Выбери категорию 👇",
        reply_markup=build_main_menu(user_id)
    )


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


@dp.message()
async def universal_handler(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    state = user_state.get(user_id)

    # Обычный вход в категорию
    if text in data_store["categories"] and not state:
        user_category[user_id] = text
        await message.answer(
            f"Категория: {text}\nВыбери текст 👇",
            reply_markup=build_category_menu(text)
        )
        return

    # Обычное нажатие текста внутри категории
    current_category = user_category.get(user_id)
    if current_category and not state:
        category_items = data_store["categories"].get(current_category, {})
        if text in category_items:
            await message.answer(category_items[text])
            return

    # -------- ДОБАВИТЬ КАТЕГОРИЮ --------
    if state == "waiting_new_category_name":
        if text in data_store["categories"]:
            await message.answer("Такая категория уже есть")
            return

        data_store["categories"][text] = {}
        save_data(data_store)

        user_state.pop(user_id, None)
        await message.answer(
            f"Категория {text} добавлена ✅",
            reply_markup=build_main_menu(user_id)
        )
        return

    # -------- ДОБАВИТЬ ТЕКСТ --------
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

    # -------- ИЗМЕНИТЬ ТЕКСТ --------
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
        if text not in data_store["categories"][category]:
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

    # -------- УДАЛИТЬ ТЕКСТ --------
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
        if text not in data_store["categories"][category]:
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

    # -------- УДАЛИТЬ КАТЕГОРИЮ --------
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
