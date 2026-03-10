"""
modules/crm_fans.py

CRM модуль для aiogram 3.
Подходит под текущий bot.py пользователя без изменений:
    from modules.crm_fans import router as crm_router

Что умеет:
- /crm
- /fan @u123456789
- просто отправить: @u123456789
- /addfan @u123456789
- /setmodel @u123456789|@ashley_bambyv
- /note @u123456789|@ashley_bambyv|получил кастом
- /purchase @u123456789|@ashley_bambyv|custom video|150
- /fans @ashley_bambyv
- /fanstats
- /delfan @u123456789

Структура хранения:
data/fans.json

Формат:
{
  "fans": [
    {
      "username": "@u123",
      "models": [
        {
          "model": "@ashley_bambyv",
          "spent": 150,
          "last_purchase": "10.03.2026",
          "notes": ["..."],
          "purchases": [{"name": "custom", "price": 150, "date": "10.03.2026"}]
        }
      ],
      "created": "10.03.2026",
      "updated_at": "2026-03-10T20:00:00"
    }
  ]
}
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router(name="crm_fans_router")


# =========================
# helpers
# =========================

def _today_string() -> str:
    return datetime.now().strftime("%d.%m.%Y")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _money(value: Any) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "0"
    if num.is_integer():
        return str(int(num))
    return f"{num:.2f}"


def _normalize_username(username: str) -> str:
    username = str(username).strip().lower()
    if not username:
        return ""
    if not username.startswith("@"):
        username = f"@{username}"
    return username


def _normalize_model(model: str) -> str:
    model = str(model).strip().lower()
    if not model:
        return ""
    if not model.startswith("@"):
        model = f"@{model}"
    return model


def _get_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "").strip()
    if not raw:
        return set()

    result: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.add(int(part))
    return result


def _is_allowed(user_id: int) -> bool:
    admins = _get_admin_ids()
    if not admins:
        return True
    return user_id in admins


# =========================
# storage
# =========================

class FanCRM:
    def __init__(self, db_file: str = "data/fans.json") -> None:
        self.db_file = Path(db_file)
        self.data = self._load()

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.db_file.exists():
            return {"fans": []}

        try:
            with self.db_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {"fans": []}
            fans = data.get("fans", [])
            if not isinstance(fans, list):
                return {"fans": []}
            return {"fans": fans}
        except (OSError, json.JSONDecodeError):
            return {"fans": []}

    def save(self) -> None:
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        with self.db_file.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def all_fans(self) -> List[Dict[str, Any]]:
        return self.data.setdefault("fans", [])

    def get_fan(self, username: str) -> Optional[Dict[str, Any]]:
        username = _normalize_username(username)
        if not username:
            return None

        for fan in self.all_fans():
            if _normalize_username(fan.get("username", "")) == username:
                fan.setdefault("models", [])
                fan.setdefault("created", "—")
                fan.setdefault("updated_at", _now_iso())
                return fan
        return None

    def add_fan(self, username: str) -> tuple[bool, str]:
        username = _normalize_username(username)
        if not username.startswith("@u"):
            return False, "Username фаната должен быть в формате @u123456"

        if self.get_fan(username):
            return False, "Фанат уже существует"

        self.all_fans().append(
            {
                "username": username,
                "models": [],
                "created": _today_string(),
                "updated_at": _now_iso(),
            }
        )
        self.save()
        return True, "Фанат добавлен"

    def delete_fan(self, username: str) -> tuple[bool, str]:
        username = _normalize_username(username)
        fans = self.all_fans()
        for i, fan in enumerate(fans):
            if _normalize_username(fan.get("username", "")) == username:
                del fans[i]
                self.save()
                return True, "Фанат удален"
        return False, "Фанат не найден"

    def _get_or_create_model_entry(self, fan: Dict[str, Any], model: str) -> Dict[str, Any]:
        model = _normalize_model(model)
        fan.setdefault("models", [])

        for item in fan["models"]:
            if _normalize_model(item.get("model", "")) == model:
                item.setdefault("spent", 0)
                item.setdefault("last_purchase", "—")
                item.setdefault("notes", [])
                item.setdefault("purchases", [])
                return item

        entry = {
            "model": model,
            "spent": 0,
            "last_purchase": "—",
            "notes": [],
            "purchases": [],
        }
        fan["models"].append(entry)
        return entry

    def set_model(self, username: str, model: str) -> tuple[bool, str]:
        fan = self.get_fan(username)
        if not fan:
            ok, _ = self.add_fan(username)
            if not ok:
                return False, "Не удалось создать фаната"
            fan = self.get_fan(username)

        self._get_or_create_model_entry(fan, model)
        fan["updated_at"] = _now_iso()
        self.save()
        return True, "Модель добавлена"

    def add_note(self, username: str, model: str, note: str) -> tuple[bool, str]:
        fan = self.get_fan(username)
        if not fan:
            ok, _ = self.add_fan(username)
            if not ok:
                return False, "Не удалось создать фаната"
            fan = self.get_fan(username)

        note = str(note).strip()
        if not note:
            return False, "Пустая заметка"

        entry = self._get_or_create_model_entry(fan, model)
        entry.setdefault("notes", []).append(note)
        fan["updated_at"] = _now_iso()
        self.save()
        return True, "Заметка добавлена"

    def add_purchase(self, username: str, model: str, name: str, price: float) -> tuple[bool, str]:
        fan = self.get_fan(username)
        if not fan:
            ok, _ = self.add_fan(username)
            if not ok:
                return False, "Не удалось создать фаната"
            fan = self.get_fan(username)

        entry = self._get_or_create_model_entry(fan, model)
        purchase = {
            "name": str(name).strip() or "Без названия",
            "price": float(price),
            "date": _today_string(),
        }
        entry.setdefault("purchases", []).append(purchase)
        entry["spent"] = round(sum(float(p.get("price", 0)) for p in entry["purchases"]), 2)
        entry["last_purchase"] = _today_string()
        fan["updated_at"] = _now_iso()
        self.save()
        return True, "Покупка добавлена"

    def fans_by_model(self, model: str) -> List[Dict[str, Any]]:
        model = _normalize_model(model)
        result: List[Dict[str, Any]] = []

        for fan in self.all_fans():
            for item in fan.get("models", []):
                if _normalize_model(item.get("model", "")) == model:
                    result.append(
                        {
                            "username": fan.get("username", "—"),
                            "model": model,
                            "spent": item.get("spent", 0),
                            "last_purchase": item.get("last_purchase", "—"),
                            "notes_count": len(item.get("notes", [])),
                        }
                    )
                    break

        result.sort(key=lambda x: float(x.get("spent", 0)), reverse=True)
        return result

    def total_spent(self, fan: Dict[str, Any]) -> float:
        return round(sum(float(item.get("spent", 0)) for item in fan.get("models", [])), 2)

    def format_fan_card(self, fan: Dict[str, Any]) -> str:
        models = fan.get("models", []) or []
        total = self.total_spent(fan)

        lines = [
            f"👤 FAN: {fan.get('username', '—')}",
            "",
            f"💰 Всего потратил: ${_money(total)}",
            f"👩 Моделей: {len(models)}",
            "",
        ]

        if not models:
            lines.append("Пока нет привязанных моделей и комментариев.")
            return "\n".join(lines)

        models_sorted = sorted(models, key=lambda x: float(x.get("spent", 0)), reverse=True)

        for item in models_sorted:
            model = item.get("model", "—")
            spent = item.get("spent", 0)
            last_purchase = item.get("last_purchase", "—")
            notes = item.get("notes", []) or []
            purchases = item.get("purchases", []) or []

            lines.append(f"📌 {model}")
            lines.append(f"Потратил: ${_money(spent)}")
            lines.append(f"Последний заказ: {last_purchase}")

            if purchases:
                last_purchases = purchases[-3:]
                lines.append("Покупки:")
                for p in last_purchases:
                    lines.append(f"• {p.get('name', 'Без названия')} — ${_money(p.get('price', 0))}")
            else:
                lines.append("Покупки: —")

            if notes:
                lines.append("Заметки:")
                for note in notes[-5:]:
                    lines.append(f"• {note}")
            else:
                lines.append("Заметки: —")

            lines.append("")

        return "\n".join(lines).strip()

    def format_model_list(self, model: str, fans: List[Dict[str, Any]]) -> str:
        model = _normalize_model(model) or model

        if not fans:
            return f"По модели {model} никого не найдено"

        lines = [f"👩 Модель: {model}", ""]
        for i, fan in enumerate(fans, start=1):
            lines.append(
                f"{i}. {fan.get('username', '—')} — ${_money(fan.get('spent', 0))} | "
                f"заметок: {fan.get('notes_count', 0)} | последний заказ: {fan.get('last_purchase', '—')}"
            )
        return "\n".join(lines)

    def stats(self) -> Dict[str, Any]:
        fans = self.all_fans()
        total_fans = len(fans)
        total_revenue = round(sum(self.total_spent(fan) for fan in fans), 2)

        top_fan = None
        if fans:
            top_fan = max(fans, key=self.total_spent)

        by_model: Dict[str, float] = {}
        for fan in fans:
            for item in fan.get("models", []):
                model = item.get("model", "—") or "—"
                by_model[model] = by_model.get(model, 0.0) + float(item.get("spent", 0))

        return {
            "total_fans": total_fans,
            "total_revenue": total_revenue,
            "top_fan": top_fan,
            "by_model": by_model,
        }


crm = FanCRM(os.getenv("FAN_CRM_DB", "data/fans.json"))


# =========================
# keyboards
# =========================

def crm_main_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔎 Найти фана", callback_data="crm_help_fan")
    kb.button(text="➕ Добавить фана", callback_data="crm_help_addfan")
    kb.button(text="📝 Добавить заметку", callback_data="crm_help_note")
    kb.button(text="💸 Добавить покупку", callback_data="crm_help_purchase")
    kb.button(text="👩 Фаны модели", callback_data="crm_help_fans")
    kb.button(text="📊 Статистика", callback_data="crm_stats")
    kb.adjust(2, 2, 2)
    return kb.as_markup()


def fan_card_kb(username: str) -> InlineKeyboardMarkup:
    encoded = _normalize_username(username).replace("@", "")
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Как добавить заметку", callback_data=f"crm_note_hint_{encoded}")
    kb.button(text="💸 Как добавить покупку", callback_data=f"crm_purchase_hint_{encoded}")
    kb.button(text="🔄 Обновить", callback_data=f"crm_refresh_{encoded}")
    kb.adjust(1, 1, 1)
    return kb.as_markup()


# =========================
# commands
# =========================

@router.message(Command("crm"))
async def crm_menu(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    text = (
        "📂 CRM меню\n\n"
        "Главный поиск работает по username фаната:\n"
        "@u364670687\n\n"
        "Команды:\n"
        "/fan @u364670687\n"
        "/addfan @u364670687\n"
        "/setmodel @u364670687|@ashley_bambyv\n"
        "/note @u364670687|@ashley_bambyv|получил кастом\n"
        "/purchase @u364670687|@ashley_bambyv|custom video|150\n"
        "/fans @ashley_bambyv\n"
        "/fanstats\n"
        "/delfan @u364670687\n\n"
        "Также можно просто отправить:\n"
        "@u364670687"
    )
    await message.answer(text, reply_markup=crm_main_kb())


@router.message(Command("fan"))
async def fan_lookup(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат:\n/fan @u364670687")
        return

    username = parts[1].strip()
    fan = crm.get_fan(username)
    if not fan:
        await message.answer("Фанат не найден")
        return

    await message.answer(
        crm.format_fan_card(fan),
        reply_markup=fan_card_kb(fan["username"]),
    )


@router.message(Command("addfan"))
async def add_fan_handler(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат:\n/addfan @u364670687")
        return

    ok, msg = crm.add_fan(parts[1].strip())
    await message.answer(msg)


@router.message(Command("setmodel"))
async def set_model_handler(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    payload = (message.text or "").replace("/setmodel", "", 1).strip()
    if "|" not in payload:
        await message.answer("Формат:\n/setmodel @u364670687|@ashley_bambyv")
        return

    username, model = [x.strip() for x in payload.split("|", 1)]
    ok, msg = crm.set_model(username, model)
    await message.answer(msg)


@router.message(Command("note"))
async def add_note_handler(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    payload = (message.text or "").replace("/note", "", 1).strip()
    parts = [x.strip() for x in payload.split("|")]

    if len(parts) < 3:
        await message.answer("Формат:\n/note @u364670687|@ashley_bambyv|сказал что все понравилось")
        return

    username, model, note = parts[0], parts[1], "|".join(parts[2:]).strip()
    ok, msg = crm.add_note(username, model, note)
    await message.answer(msg)


@router.message(Command("purchase"))
async def add_purchase_handler(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    payload = (message.text or "").replace("/purchase", "", 1).strip()
    parts = [x.strip() for x in payload.split("|")]

    if len(parts) < 4:
        await message.answer("Формат:\n/purchase @u364670687|@ashley_bambyv|custom video|150")
        return

    username, model, purchase_name, price_raw = parts[0], parts[1], parts[2], parts[3]

    try:
        price = float(price_raw.replace(",", "."))
    except ValueError:
        await message.answer("Цена должна быть числом")
        return

    ok, msg = crm.add_purchase(username, model, purchase_name, price)
    await message.answer(msg)


@router.message(Command("fans"))
async def fans_by_model_handler(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат:\n/fans @ashley_bambyv")
        return

    model = parts[1].strip()
    fans = crm.fans_by_model(model)
    await message.answer(crm.format_model_list(model, fans))


@router.message(Command("fanstats"))
async def fan_stats_handler(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    stats = crm.stats()
    top_fan = stats.get("top_fan")

    top_text = "—"
    if top_fan:
        top_text = f"{top_fan.get('username', '—')} — ${_money(crm.total_spent(top_fan))}"

    model_lines = []
    for model, amount in sorted(stats["by_model"].items(), key=lambda x: str(x[0]).lower()):
        model_lines.append(f"• {model}: ${_money(amount)}")

    text = (
        "📊 CRM статистика\n\n"
        f"Фанов: {stats['total_fans']}\n"
        f"Общий доход: ${_money(stats['total_revenue'])}\n"
        f"Топ фан: {top_text}\n\n"
        "По моделям:\n"
        f"{chr(10).join(model_lines) if model_lines else '—'}"
    )
    await message.answer(text)


@router.message(Command("delfan"))
async def delete_fan_handler(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("Нет доступа")
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат:\n/delfan @u364670687")
        return

    ok, msg = crm.delete_fan(parts[1].strip())
    await message.answer(msg)


# =========================
# auto lookup by plain text
# =========================

@router.message(F.text.regexp(r"^@u\d{5,}$"))
async def plain_username_lookup(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return

    username = (message.text or "").strip()
    fan = crm.get_fan(username)
    if not fan:
        await message.answer("Фанат не найден")
        return

    await message.answer(
        crm.format_fan_card(fan),
        reply_markup=fan_card_kb(fan["username"]),
    )


# =========================
# callbacks
# =========================

@router.callback_query(F.data == "crm_stats")
async def crm_stats_callback(callback: CallbackQuery) -> None:
    if not _is_allowed(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    stats = crm.stats()
    top_fan = stats.get("top_fan")
    top_text = "—"
    if top_fan:
        top_text = f"{top_fan.get('username', '—')} — ${_money(crm.total_spent(top_fan))}"

    model_lines = []
    for model, amount in sorted(stats["by_model"].items(), key=lambda x: str(x[0]).lower()):
        model_lines.append(f"• {model}: ${_money(amount)}")

    text = (
        "📊 CRM статистика\n\n"
        f"Фанов: {stats['total_fans']}\n"
        f"Общий доход: ${_money(stats['total_revenue'])}\n"
        f"Топ фан: {top_text}\n\n"
        "По моделям:\n"
        f"{chr(10).join(model_lines) if model_lines else '—'}"
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("crm_refresh_"))
async def refresh_fan_callback(callback: CallbackQuery) -> None:
    if not _is_allowed(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    encoded = callback.data.replace("crm_refresh_", "", 1)
    username = f"@{encoded}"
    fan = crm.get_fan(username)
    if not fan:
        await callback.answer("Фанат не найден", show_alert=True)
        return

    await callback.message.edit_text(
        crm.format_fan_card(fan),
        reply_markup=fan_card_kb(fan["username"]),
    )
    await callback.answer("Обновлено")


@router.callback_query(F.data.startswith("crm_note_hint_"))
async def note_hint_callback(callback: CallbackQuery) -> None:
    if not _is_allowed(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    encoded = callback.data.replace("crm_note_hint_", "", 1)
    await callback.message.answer(
        f"Добавь заметку так:\n/note @{encoded}|@ashley_bambyv|сказал что вечером хочет играть"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("crm_purchase_hint_"))
async def purchase_hint_callback(callback: CallbackQuery) -> None:
    if not _is_allowed(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    encoded = callback.data.replace("crm_purchase_hint_", "", 1)
    await callback.message.answer(
        f"Добавь покупку так:\n/purchase @{encoded}|@ashley_bambyv|custom video|150"
    )
    await callback.answer()


@router.callback_query(F.data == "crm_help_fan")
async def help_fan_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("🔎 Поиск:\n/fan @u364670687\nили просто отправь\n@u364670687")
    await callback.answer()


@router.callback_query(F.data == "crm_help_addfan")
async def help_addfan_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("➕ Добавить фана:\n/addfan @u364670687")
    await callback.answer()


@router.callback_query(F.data == "crm_help_note")
async def help_note_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("📝 Добавить заметку:\n/note @u364670687|@ashley_bambyv|получил кастом")
    await callback.answer()


@router.callback_query(F.data == "crm_help_purchase")
async def help_purchase_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("💸 Добавить покупку:\n/purchase @u364670687|@ashley_bambyv|custom video|150")
    await callback.answer()


@router.callback_query(F.data == "crm_help_fans")
async def help_fans_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("👩 Фаны модели:\n/fans @ashley_bambyv")
    await callback.answer()
