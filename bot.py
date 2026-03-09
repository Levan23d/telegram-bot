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

user_state = {}
temp_data = {}


def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "buttons": {
                "🍑 ANAL": "Текст для ANAL",
                "🍆 DILDO": "Текст для DILDO",
                "💬 SEXTING": "Текст для SEXTING",
                "📹 VIDEOCALL": "Текст для VIDEOCALL",
                "⭐ DICK RATE": "Текст для DICK RATE",
                "✋ FINGERS": "Текст для FINGERS"
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


def build_keyboard(user_id: int):
    buttons = list(data_store["buttons"].keys())

    rows = []
    row = []

    for btn in buttons:
        row.append(KeyboardButton(text=btn))
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    if is_admin(user_id):
        rows.append([KeyboardButton(text="➕ Добавить кнопку"), KeyboardButton(text="✏️ Изменить текст")])
        rows.append([KeyboardButton(text="🗑 Удалить кнопку"), KeyboardButton(text="📋 Список кнопок")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@dp.message(F.text == "/start")
async def start_handler(message: Message):
    user_state.pop(message.from_user.id, None)
    temp_data.pop(message.from_user.id, None)
    await message.answer("Главное меню", reply_markup=build_keyboard(message.from_user.id))


@dp.message(F.text == "📋 Список кнопок")
async def list_buttons_handler(message: Message):
    if not is_admin(message.from_user.id):
        return

    if not data_store["buttons"]:
        await message.answer("Кнопок пока нет")
        return

    text = "Кнопки в меню:\n\n" + "\n".join(f"• {name}" for name in data_store["buttons"].keys())
    await message.answer(text)


@dp.message(F.text == "➕ Добавить кнопку")
async def add_button_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_button_name"
    await message.answer("Отправь название новой кнопки")


@dp.message(F.text == "✏️ Изменить текст")
async def edit_text_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_edit_button_name"
    await message.answer("Отправь точное название кнопки, у которой нужно изменить текст")


@dp.message(F.text == "🗑 Удалить кнопку")
async def delete_button_start(message: Message):
    if not is_admin(message.from_user.id):
        return

    user_state[message.from_user.id] = "waiting_delete_button_name"
    await message.answer("Отправь точное название кнопки, которую нужно удалить")


@dp.message()
async def universal_handler(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    state = user_state.get(user_id)

    if text in data_store["buttons"] and not state:
        await message.answer(data_store["buttons"][text])
        return

    if state == "waiting_button_name":
        if text in data_store["buttons"]:
            await message.answer("Такая кнопка уже есть")
            return

        temp_data[user_id] = {"button_name": text}
        user_state[user_id] = "waiting_button_text"
        await message.answer(f"Теперь отправь текст для кнопки: {text}")
        return

    if state == "waiting_button_text":
        button_name = temp_data[user_id]["button_name"]
        data_store["buttons"][button_name] = text
        save_data(data_store)

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer(
            f"Кнопка {button_name} добавлена ✅",
            reply_markup=build_keyboard(user_id)
        )
        return

    if state == "waiting_edit_button_name":
        if text not in data_store["buttons"]:
            await message.answer("Такой кнопки нет")
            return

        temp_data[user_id] = {"button_name": text}
        user_state[user_id] = "waiting_new_text_for_button"
        await message.answer(f"Отправь новый текст для кнопки: {text}")
        return

    if state == "waiting_new_text_for_button":
        button_name = temp_data[user_id]["button_name"]
        data_store["buttons"][button_name] = text
        save_data(data_store)

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer(
            f"Текст для {button_name} обновлён ✅",
            reply_markup=build_keyboard(user_id)
        )
        return

    if state == "waiting_delete_button_name":
        if text not in data_store["buttons"]:
            await message.answer("Такой кнопки нет")
            return

        del data_store["buttons"][text]
        save_data(data_store)

        user_state.pop(user_id, None)

        await message.answer(
            f"Кнопка {text} удалена ✅",
            reply_markup=build_keyboard(user_id)
        )
        return

    await message.answer("Нажми кнопку из меню", reply_markup=build_keyboard(user_id))


async def main():
    if not TOKEN:
        raise ValueError("Переменная окружения BOT_TOKEN не задана")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
