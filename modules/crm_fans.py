from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.event.bases import SkipHandler

from database import add_fan_db, add_purchase_db, fan_exists, get_fan_by_id, get_crm_stats, search_fans
from state import user_state, temp_data

router = Router()


def build_fans_menu():
    rows = [
        [KeyboardButton(text="➕ Добавить фаната"), KeyboardButton(text="💸 Добавить покупку")],
        [KeyboardButton(text="🔎 Найти фаната"), KeyboardButton(text="📊 Статистика CRM")],
        [KeyboardButton(text="⬅ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def format_fan_card(fan):
    fan_id, username, model_name, interests, notes, total_spent, created_at = fan

    return (
        f"👤 Карточка фаната\n\n"
        f"ID: {fan_id}\n"
        f"Username: {username or '—'}\n"
        f"Модель: {model_name or '—'}\n"
        f"Интересы: {interests or '—'}\n"
        f"Заметка: {notes or '—'}\n"
        f"Потрачено: {total_spent or 0}$\n"
        f"Создан: {created_at}"
    )


@router.message(F.text == "👤 Фанаты")
async def fans_menu_handler(message: Message):
    user_state.pop(message.from_user.id, None)
    temp_data.pop(message.from_user.id, None)
    await message.answer("CRM фанатов", reply_markup=build_fans_menu())


@router.message(F.text == "📊 Статистика CRM")
async def crm_stats_handler(message: Message):
    fans_count, purchases_count, total_sum = get_crm_stats()
    await message.answer(
        f"📊 CRM статистика\n\n"
        f"Фанатов: {fans_count}\n"
        f"Покупок: {purchases_count}\n"
        f"Общая сумма: {total_sum}$",
        reply_markup=build_fans_menu()
    )


@router.message(F.text == "➕ Добавить фаната")
async def add_fan_start(message: Message):
    user_state[message.from_user.id] = "crm_fan_username"
    temp_data[message.from_user.id] = {}
    await message.answer("Введи username фаната")


@router.message(F.text == "💸 Добавить покупку")
async def add_purchase_start(message: Message):
    user_state[message.from_user.id] = "crm_purchase_fan_id"
    temp_data[message.from_user.id] = {}
    await message.answer("Введи ID фаната")


@router.message(F.text == "🔎 Найти фаната")
async def find_fan_start(message: Message):
    user_state[message.from_user.id] = "crm_find_fan"
    await message.answer("Введи ID, username или @username фаната")


@router.message()
async def crm_flow_handler(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if not state or not str(state).startswith("crm_"):
        raise SkipHandler()

    if state == "crm_find_fan":
        results = search_fans(text)

        if not results:
            await message.answer("Фанат не найден", reply_markup=build_fans_menu())
            return

        if len(results) == 1:
            await message.answer(format_fan_card(results[0]), reply_markup=build_fans_menu())
            user_state.pop(user_id, None)
            return

        lines = ["Найдено несколько совпадений:\n"]
        for fan in results[:20]:
            fan_id, username, model_name, interests, notes, total_spent, created_at = fan
            lines.append(f"{fan_id} | {username or '—'} | {model_name or '—'}")

        lines.append("\nВведи ID, чтобы открыть карточку")
        await message.answer("\n".join(lines), reply_markup=build_fans_menu())
        user_state[user_id] = "crm_find_fan_pick_id"
        return

    if state == "crm_find_fan_pick_id":
        if not text.isdigit():
            await message.answer("Введи именно ID цифрами", reply_markup=build_fans_menu())
            return

        fan = get_fan_by_id(int(text))
        if not fan:
            await message.answer("Фанат не найден", reply_markup=build_fans_menu())
            return

        await message.answer(format_fan_card(fan), reply_markup=build_fans_menu())
        user_state.pop(user_id, None)
        return

    if state == "crm_fan_username":
        temp_data[user_id]["username"] = text.lower()
        user_state[user_id] = "crm_fan_model"
        await message.answer("Модель")
        return

    if state == "crm_fan_model":
        temp_data[user_id]["model_name"] = text
        user_state[user_id] = "crm_fan_interests"
        await message.answer("Интересы")
        return

    if state == "crm_fan_interests":
        temp_data[user_id]["interests"] = text
        user_state[user_id] = "crm_fan_notes"
        await message.answer("Заметка")
        return

    if state == "crm_fan_notes":
        fan_id = add_fan_db(
            temp_data[user_id]["username"],
            temp_data[user_id]["model_name"],
            temp_data[user_id]["interests"],
            text
        )
        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)
        await message.answer(f"Фанат добавлен ID {fan_id}", reply_markup=build_fans_menu())
        return

    if state == "crm_purchase_fan_id":
        if not text.isdigit():
            await message.answer("ID должен быть числом")
            return

        fan_id = int(text)
        if not fan_exists(fan_id):
            await message.answer("Фанат с таким ID не найден")
            return

        temp_data[user_id]["fan_id"] = fan_id
        user_state[user_id] = "crm_purchase_item"
        await message.answer("Что купил?")
        return

    if state == "crm_purchase_item":
        temp_data[user_id]["item_name"] = text
        user_state[user_id] = "crm_purchase_amount"
        await message.answer("Сумма покупки")
        return

    if state == "crm_purchase_amount":
        try:
            amount = float(text.replace(",", "."))
        except ValueError:
            await message.answer("Введи сумму числом")
            return

        add_purchase_db(temp_data[user_id]["fan_id"], temp_data[user_id]["item_name"], amount)

        fan_id = temp_data[user_id]["fan_id"]
        item_name = temp_data[user_id]["item_name"]

        user_state.pop(user_id, None)
        temp_data.pop(user_id, None)

        await message.answer(
            f"Покупка добавлена\n\nID: {fan_id}\nТовар: {item_name}\nСумма: {amount}$",
            reply_markup=build_fans_menu()
        )
        return

    raise SkipHandler()
