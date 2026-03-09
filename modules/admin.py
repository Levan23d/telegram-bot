from aiogram import Router, F
from aiogram.types import Message
from aiogram.dispatcher.event.bases import SkipHandler

from config import ADMIN_ID
from state import data_store, save_data, user_state, temp_data

router = Router()


@router.message(F.text == "➕ Категория")
async def add_category_start(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_state[message.from_user.id] = "new_category"

    await message.answer("Отправь название новой категории")


@router.message(F.text == "➕ Текст")
async def add_text_start(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    user_state[message.from_user.id] = "choose_category"

    await message.answer("В какую категорию добавить текст?")


@router.message()
async def admin_handler(message: Message):

    user_id = message.from_user.id
    text = message.text

    if user_id != ADMIN_ID:
        raise SkipHandler()

    state = user_state.get(user_id)

    if not state:
        raise SkipHandler()

    if state == "new_category":

        data_store["categories"][text] = {}

        save_data(data_store)

        user_state.pop(user_id, None)

        await message.answer(f"Категория {text} добавлена")
        return

    elif state == "choose_category":

        if text not in data_store["categories"]:
            await message.answer("Категория не найдена")
            return

        temp_data[user_id] = {"category": text}
        user_state[user_id] = "text_name"

        await message.answer("Название кнопки")
        return

    elif state == "text_name":

        temp_data[user_id]["button"] = text
        user_state[user_id] = "text_value"

        await message.answer("Теперь отправь сам текст")
        return

    elif state == "text_value":

        category = temp_data[user_id]["category"]
        button = temp_data[user_id]["button"]

        data_store["categories"][category][button] = text

        save_data(data_store)

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer("Текст добавлен")
        return

    raise SkipHandler()
