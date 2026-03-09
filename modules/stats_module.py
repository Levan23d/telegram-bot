from aiogram import Router, F
from aiogram.types import Message

from config import ADMIN_ID
from state import stats_store

router = Router()


@router.message(F.text == " Статистика")
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


@router.message(F.text == " Пользователи")
async def users_handler(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    users = stats_store["users"]

    if not users:
        await message.answer("Пользователей пока нет")
        return

    lines = []

    for uid, info in list(users.items())[:30]:

        starts = info.get("starts", 0)

        lines.append(
            f"ID: {uid} | Starts: {starts}"
        )

    text = "👥 Пользователи:\n\n" + "\n".join(lines)

    await message.answer(text)
