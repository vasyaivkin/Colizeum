"""Handlers for коммуналка — electricity meter readings."""

import datetime
import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, desc

from bot.models.database import async_session
from bot.models.models import Utility
from bot.states.states import UtilityStates
from bot.keyboards.main_menu import confirm_or_manual_kb, receipt_ask_kb
from bot.services.settings_service import get_float_setting
from bot.services.management_sheets import append_utility_row
from bot.services.google_drive import upload_receipt, build_receipt_filename
from bot.utils.dates import format_date, today_msk, format_date_short
from bot.utils.formatting import fmt_int

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("коммуналка"))
@router.message(F.text == "💡 Коммуналка")
async def cmd_utility(message: Message, state: FSMContext):
    """Начало диалога ввода коммуналки или просмотр истории."""
    text = message.text.strip()

    # Если "/коммуналка последняя" — показать последние показания
    if "последн" in text.lower():
        await _show_last_readings(message)
        return

    # Если просто "/коммуналка" без дополнений — показать историю
    if text in ("/коммуналка", "💡 Коммуналка", "/kommunalka"):
        # Предлагаем два варианта: внести новые или посмотреть историю
        await state.clear()
        await message.answer(
            "💡 Счётчик Т1 (день) — введите текущие показания:"
        )
        await state.set_state(UtilityStates.t1_reading)
        return


@router.message(Command("коммуналка_история"))
async def cmd_utility_history(message: Message):
    """Показать историю коммуналки."""
    await _show_history(message)


# --- Шаг 1: Показания Т1 ---

@router.message(UtilityStates.t1_reading)
async def process_t1(message: Message, state: FSMContext):
    try:
        t1 = float(message.text.strip().replace(" ", "").replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число — показания Т1 (день):")
        return

    await state.update_data(t1_reading=t1)
    await message.answer("Счётчик Т2 (ночь) — введите текущие показания:")
    await state.set_state(UtilityStates.t2_reading)


# --- Шаг 2: Показания Т2 ---

@router.message(UtilityStates.t2_reading)
async def process_t2(message: Message, state: FSMContext):
    try:
        t2 = float(message.text.strip().replace(" ", "").replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число — показания Т2 (ночь):")
        return

    await state.update_data(t2_reading=t2)

    # Получаем предыдущие показания и тарифы
    async with async_session() as session:
        result = await session.execute(
            select(Utility).order_by(desc(Utility.id)).limit(1)
        )
        prev = result.scalar_one_or_none()

        t1_rate = await get_float_setting(session, "t1_tariff")
        t2_rate = await get_float_setting(session, "t2_tariff")

    data = await state.get_data()
    t1 = data["t1_reading"]

    if prev:
        t1_kwh = t1 - prev.t1_reading
        t2_kwh = t2 - prev.t2_reading
        t1_amount = t1_kwh * t1_rate
        t2_amount = t2_kwh * t2_rate
        total = t1_amount + t2_amount

        await state.update_data(
            t1_prev=prev.t1_reading, t2_prev=prev.t2_reading,
            t1_kwh=t1_kwh, t2_kwh=t2_kwh,
            t1_rate=t1_rate, t2_rate=t2_rate,
            t1_amount=t1_amount, t2_amount=t2_amount,
            calculated_total=total,
        )

        await message.answer(
            f"⚡ Расчёт:\n"
            f"Т1 (день): +{t1_kwh:.0f} кВт·ч × {t1_rate} = {fmt_int(t1_amount)}\n"
            f"Т2 (ночь): +{t2_kwh:.0f} кВт·ч × {t2_rate} = {fmt_int(t2_amount)}\n"
            f"Итого: {fmt_int(total)}\n\n"
            f"По тарифу: {fmt_int(total)}",
            reply_markup=confirm_or_manual_kb(),
        )
    else:
        # Нет предыдущих — это первый ввод
        await state.update_data(
            t1_prev=0, t2_prev=0,
            t1_kwh=0, t2_kwh=0,
            t1_rate=t1_rate, t2_rate=t2_rate,
            t1_amount=0, t2_amount=0,
            calculated_total=0,
        )
        await message.answer(
            "Это первый ввод показаний. Расход кВт·ч будет рассчитан при следующем вводе.\n"
            "Введите фактическую сумму (или 0 для первичной фиксации):"
        )
        await state.set_state(UtilityStates.manual_amount)

    await state.set_state(UtilityStates.confirm_amount)


# --- Шаг 3: Подтвердить или ввести вручную ---

@router.callback_query(UtilityStates.confirm_amount, F.data.startswith("utility_confirm:"))
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]

    if choice == "yes":
        data = await state.get_data()
        await state.update_data(final_total=data["calculated_total"])
        await callback.message.edit_text(
            "Прикрепить скрин/чек?",
            reply_markup=receipt_ask_kb(),
        )
        await state.set_state(UtilityStates.receipt_ask)
    else:
        await callback.message.edit_text("Введите фактическую сумму:")
        await state.set_state(UtilityStates.manual_amount)

    await callback.answer()


# --- Шаг 3а: Ручная сумма ---

@router.message(UtilityStates.manual_amount)
async def process_manual(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(" ", "").replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число:")
        return

    await state.update_data(final_total=amount, manual_total=amount)
    await message.answer(
        "Прикрепить скрин/чек?",
        reply_markup=receipt_ask_kb(),
    )
    await state.set_state(UtilityStates.receipt_ask)


# --- Шаг 4: Чек ---

@router.callback_query(UtilityStates.receipt_ask, F.data.startswith("receipt:"))
async def process_receipt_ask(callback: CallbackQuery, state: FSMContext):
    if callback.data.split(":")[1] == "yes":
        await callback.message.edit_text("📸 Пришлите фото/скрин:")
        await state.set_state(UtilityStates.receipt_photo)
    else:
        await _save_utility(callback.message, state, callback.from_user.id)
    await callback.answer()


@router.message(UtilityStates.receipt_photo, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_data = await message.bot.download_file(file.file_path)
    photo_bytes = file_data.read()

    try:
        date_str = format_date_short(today_msk())
        filename = build_receipt_filename(date_str, "коммуналка", data.get("final_total", 0))
        file_id, web_link = upload_receipt(photo_bytes, filename)
        await state.update_data(receipt_url=web_link)
    except Exception as e:
        logger.error(f"Ошибка загрузки чека коммуналки: {e}")
        await message.answer(f"⚠ Не удалось загрузить: {e}")

    await _save_utility(message, state, message.from_user.id)


# --- Сохранение ---

async def _save_utility(message: Message, state: FSMContext, user_id: int):
    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        utility = Utility(
            date=datetime.datetime.now(),
            t1_reading=data["t1_reading"],
            t2_reading=data["t2_reading"],
            t1_prev=data.get("t1_prev"),
            t2_prev=data.get("t2_prev"),
            t1_kwh=data.get("t1_kwh"),
            t2_kwh=data.get("t2_kwh"),
            t1_rate=data.get("t1_rate", 0),
            t2_rate=data.get("t2_rate", 0),
            t1_amount=data.get("t1_amount"),
            t2_amount=data.get("t2_amount"),
            total=data.get("final_total", 0),
            manual_total=data.get("manual_total"),
            receipt_url=data.get("receipt_url", ""),
            created_by=user_id,
        )
        session.add(utility)
        await session.commit()

    # Записываем в Sheets
    try:
        date_str = format_date(today_msk())
        receipt_link = data.get("receipt_url", "")
        receipt_cell = ""
        if receipt_link:
            receipt_cell = f'=HYPERLINK("{receipt_link}", "📎")'
        append_utility_row([
            date_str,
            data["t1_reading"], data["t2_reading"],
            data.get("t1_kwh", 0), data.get("t2_kwh", 0),
            data.get("t1_rate", 0), data.get("t2_rate", 0),
            data.get("t1_amount", 0), data.get("t2_amount", 0),
            data.get("final_total", 0),
            receipt_cell,
        ])
    except Exception as e:
        logger.error(f"Ошибка записи коммуналки в Sheets: {e}")

    receipt_icon = " 📎" if data.get("receipt_url") else ""
    await message.answer(
        f"✅ Записано{receipt_icon}\n\n"
        f"💡 Т1: {data['t1_reading']} → +{data.get('t1_kwh', 0):.0f} кВт·ч\n"
        f"🌙 Т2: {data['t2_reading']} → +{data.get('t2_kwh', 0):.0f} кВт·ч\n"
        f"Итого: {fmt_int(data.get('final_total', 0))}"
    )


async def _show_last_readings(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Utility).order_by(desc(Utility.id)).limit(1)
        )
        last = result.scalar_one_or_none()

    if not last:
        await message.answer("Нет данных о показаниях.")
        return

    await message.answer(
        f"💡 Последние показания ({format_date(last.date.date())}):\n"
        f"Т1 (день): {last.t1_reading}\n"
        f"Т2 (ночь): {last.t2_reading}"
    )


async def _show_history(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Utility).order_by(desc(Utility.id)).limit(12)
        )
        records = list(result.scalars().all())

    if not records:
        await message.answer("Нет данных о коммуналке.")
        return

    lines = ["💡 КОММУНАЛКА · Электричество", "═" * 30]
    for r in records:
        receipt = " 📎" if r.receipt_url else ""
        lines.append(f"\n{format_date(r.date.date())}:")
        if r.t1_kwh and r.t1_kwh > 0:
            lines.append(
                f"  Т1 (день): {r.t1_reading} → +{r.t1_kwh:.0f} кВт·ч "
                f"× {r.t1_rate} = {fmt_int(r.t1_amount or 0)}"
            )
            lines.append(
                f"  Т2 (ночь): {r.t2_reading} → +{r.t2_kwh:.0f} кВт·ч "
                f"× {r.t2_rate} = {fmt_int(r.t2_amount or 0)}"
            )
        else:
            lines.append(f"  Т1: {r.t1_reading}  Т2: {r.t2_reading}")
        lines.append(f"  Итого: {fmt_int(r.total)}{receipt}")

    await message.answer("\n".join(lines))
