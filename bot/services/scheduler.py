"""APScheduler setup for automatic reports and reminders."""

import datetime
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy import select

from config import settings
from bot.models.database import async_session
from bot.models.models import Utility, Task, User
from bot.services.google_sheets import get_shift_data
from bot.services.cash_service import get_cash_balance
from bot.services.settings_service import get_setting
from bot.utils.dates import today_msk, format_date, MONTHS_RU
from bot.utils.formatting import format_shift_report, format_daily_summary, fmt_int

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.timezone))


async def _get_chat_id() -> int | None:
    """Get the configured chat ID."""
    async with async_session() as session:
        val = await get_setting(session, "chat_id")
    if val:
        return int(val)
    return None


async def _get_all_user_ids() -> list[int]:
    """Get all active user telegram IDs."""
    async with async_session() as session:
        result = await session.execute(
            select(User.telegram_id).where(User.is_active == True)
        )
        return [r[0] for r in result.all()]


async def _send_to_all(bot: Bot, text: str):
    """Send message to all registered users."""
    user_ids = await _get_all_user_ids()
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение {uid}: {e}")


# === Авто-отчёт дневной смены (22:20) ===

async def send_day_shift_report(bot: Bot):
    """22:20 — отчёт дневной смены."""
    dt = today_msk()
    day_data = get_shift_data(dt, "day")

    if not day_data:
        return  # Нет данных — напоминание отправится в 22:40

    report = format_shift_report(
        shift_type="day",
        date_str=format_date(dt),
        admin_name=day_data["admin"],
        langame_cash=day_data["langame_cash"],
        card=day_data["card"],
        sbp=day_data["sbp"],
        terminal_cash=day_data["terminal_cash"],
        bar=day_data["bar"],
        langame_total=day_data["langame_total"],
        check_total=day_data["check_total"],
        discrepancy=day_data["discrepancy"],
        daily_total=day_data["daily_total"],
        compensation=day_data.get("compensation", 0),
        comment=day_data.get("comment", ""),
        extra_admin=day_data.get("extra_admin", ""),
    )

    await _send_to_all(bot, report)


# === Авто-отчёт ночной смены + суточный (10:30) ===

async def send_night_shift_report(bot: Bot):
    """10:30 — отчёт ночной смены + суточный итог.
    Ночная смена — за предыдущий день/текущую ночь.
    """
    dt = today_msk()
    # Ночная смена обычно относится к предыдущему дню
    yesterday = dt - datetime.timedelta(days=1)

    night_data = get_shift_data(yesterday, "night")
    if not night_data:
        night_data = get_shift_data(dt, "night")

    parts = []

    if night_data:
        night_date_str = f"{format_date(yesterday)}"
        parts.append(format_shift_report(
            shift_type="night",
            date_str=night_date_str,
            admin_name=night_data["admin"],
            langame_cash=night_data["langame_cash"],
            card=night_data["card"],
            sbp=night_data["sbp"],
            terminal_cash=night_data["terminal_cash"],
            bar=night_data["bar"],
            langame_total=night_data["langame_total"],
            check_total=night_data["check_total"],
            discrepancy=night_data["discrepancy"],
            daily_total=night_data["daily_total"],
            compensation=night_data.get("compensation", 0),
            comment=night_data.get("comment", ""),
            extra_admin=night_data.get("extra_admin", ""),
        ))

    # Суточный итог за вчера
    day_data = get_shift_data(yesterday, "day")

    # Расходы за вчера
    from bot.handlers.reports import _get_day_expenses
    expenses = await _get_day_expenses(yesterday)
    async with async_session() as session:
        cash = await get_cash_balance(session)

    warnings = []
    if not expenses or all(v == 0 for v in expenses.values()):
        warnings.append("Расходы за день не внесены")

    # Проверяем выставлены ли баллы
    # (упрощённо — если ночная смена есть, но баллы не выставлены)
    if night_data:
        from bot.models.models import Salary
        async with async_session() as session:
            start = datetime.datetime.combine(yesterday, datetime.time.min)
            end = datetime.datetime.combine(yesterday, datetime.time.max)
            result = await session.execute(
                select(Salary).where(
                    Salary.date >= start,
                    Salary.date <= end,
                    Salary.shift == "night",
                )
            )
            if not result.scalar_one_or_none():
                warnings.append(
                    f"Баллы за ночную смену ({night_data['admin']}) не выставлены"
                )

    parts.append(format_daily_summary(
        date_str=format_date(yesterday),
        day_data=day_data,
        night_data=night_data,
        expenses=expenses,
        cash_balance=cash,
        warnings=warnings,
    ))

    full_text = "\n\n".join(parts) if parts else f"📊 Нет данных за {format_date(yesterday)}"
    await _send_to_all(bot, full_text)


# === Напоминание если нет данных дневной (22:40) ===

async def remind_day_shift(bot: Bot):
    """22:40 — напоминание если нет данных дневной."""
    dt = today_msk()
    day_data = get_shift_data(dt, "day")
    if not day_data:
        await _send_to_all(bot, "⚠ Данные дневной смены не появились в таблице")


# === Напоминание если нет данных ночной (10:50) ===

async def remind_night_shift(bot: Bot):
    """10:50 — напоминание если нет данных ночной."""
    dt = today_msk()
    yesterday = dt - datetime.timedelta(days=1)
    night_data = get_shift_data(yesterday, "night")
    if not night_data:
        night_data = get_shift_data(dt, "night")
    if not night_data:
        await _send_to_all(bot, "⚠ Данные ночной смены не появились в таблице")


# === Напоминание 1-го числа (коммуналка + месяц) ===

async def monthly_reminder(bot: Bot):
    """1-е число 10:00 — напоминание закрыть месяц."""
    dt = today_msk()
    if dt.day != 1:
        return
    prev_month = dt.month - 1 if dt.month > 1 else 12
    month_name = MONTHS_RU[prev_month]
    await _send_to_all(
        bot,
        f"📅 ЕЖЕМЕСЯЧНОЕ НАПОМИНАНИЕ\n\n"
        f"1. Зафиксировать коммуналку (💡 Коммуналка)\n"
        f"2. Сверить ОФД за {month_name}\n"
        f"3. Закрыть P&L за {month_name}"
    )


# === Напоминания коммуналки 1-го числа (5 раз) ===

async def utility_reminder(bot: Bot):
    """1-е число — напоминание внести показания электричества."""
    dt = today_msk()
    if dt.day != 1:
        return

    # Проверяем, внесены ли показания за этот месяц
    async with async_session() as session:
        result = await session.execute(
            select(Utility).where(
                Utility.date >= datetime.datetime.combine(dt, datetime.time.min)
            )
        )
        if result.scalar_one_or_none():
            return  # Уже внесены — пропускаем

    await _send_to_all(
        bot,
        "💡 Напоминание: внесите показания счётчиков электричества!\n"
        "Нажмите «💡 Коммуналка» или /коммуналка"
    )


# === Напоминания о задачах ===

async def task_reminders(bot: Bot):
    """Ежедневно в 09:00 — напоминания о задачах с дедлайном."""
    dt = today_msk()
    tomorrow = dt + datetime.timedelta(days=1)

    async with async_session() as session:
        # Задачи со сроком завтра
        result = await session.execute(
            select(Task).where(
                Task.status == "pending",
                Task.deadline.isnot(None),
            )
        )
        tasks = list(result.scalars().all())

    for task in tasks:
        if not task.deadline:
            continue
        deadline_date = task.deadline.date() if isinstance(task.deadline, datetime.datetime) else task.deadline

        if deadline_date == tomorrow:
            # За день до срока
            try:
                await bot.send_message(
                    task.assignee_id or task.creator_id,
                    f"⏰ Завтра срок задачи #{task.id}\n"
                    f"{task.description}"
                )
            except Exception:
                pass
        elif deadline_date == dt:
            # В день срока
            try:
                await bot.send_message(
                    task.assignee_id or task.creator_id,
                    f"🔴 Сегодня срок задачи #{task.id}!\n"
                    f"{task.description}"
                )
                # Уведомляем и создателя
                if task.creator_id != (task.assignee_id or task.creator_id):
                    await bot.send_message(
                        task.creator_id,
                        f"🔴 Задача #{task.id} — срок сегодня, не выполнена\n"
                        f"{task.description}"
                    )
            except Exception:
                pass
        elif deadline_date < dt:
            # Просрочена — напоминаем обоим
            try:
                text = (
                    f"🔴 Задача #{task.id} ПРОСРОЧЕНА "
                    f"(срок был {format_date(deadline_date)})\n"
                    f"{task.description}"
                )
                await bot.send_message(task.assignee_id or task.creator_id, text)
                if task.creator_id != (task.assignee_id or task.creator_id):
                    await bot.send_message(task.creator_id, text)
            except Exception:
                pass


# === Гарантии оборудования ===

async def warranty_reminders(bot: Bot):
    """Ежедневно — проверка гарантий, истекающих через 7 дней."""
    from bot.models.models import Equipment

    dt = today_msk()
    warn_date = dt + datetime.timedelta(days=7)

    async with async_session() as session:
        result = await session.execute(
            select(Equipment).where(
                Equipment.warranty_until.isnot(None),
                Equipment.status != "decommissioned",
            )
        )
        items = list(result.scalars().all())

    for eq in items:
        if not eq.warranty_until:
            continue
        w_date = eq.warranty_until.date() if isinstance(eq.warranty_until, datetime.datetime) else eq.warranty_until
        if w_date == warn_date:
            await _send_to_all(
                bot,
                f"⚠ Гарантия заканчивается через 7 дней!\n"
                f"🖥 {eq.name} · {eq.store or '—'} · до {format_date(w_date)}"
            )


def setup_scheduler(bot: Bot):
    """Configure and start the scheduler."""
    tz = ZoneInfo(settings.timezone)

    # Авто-отчёт дневной смены — 22:20
    scheduler.add_job(
        send_day_shift_report, CronTrigger(hour=22, minute=20, timezone=tz),
        args=[bot], id="day_shift_report",
    )

    # Авто-отчёт ночной смены + суточный — 10:30
    scheduler.add_job(
        send_night_shift_report, CronTrigger(hour=10, minute=30, timezone=tz),
        args=[bot], id="night_shift_report",
    )

    # Напоминание дневной — 22:40
    scheduler.add_job(
        remind_day_shift, CronTrigger(hour=22, minute=40, timezone=tz),
        args=[bot], id="remind_day_shift",
    )

    # Напоминание ночной — 10:50
    scheduler.add_job(
        remind_night_shift, CronTrigger(hour=10, minute=50, timezone=tz),
        args=[bot], id="remind_night_shift",
    )

    # Месячное напоминание — 1-е число 10:00
    scheduler.add_job(
        monthly_reminder, CronTrigger(day=1, hour=10, minute=0, timezone=tz),
        args=[bot], id="monthly_reminder",
    )

    # Коммуналка — 1-е число: 09:00, 12:00, 15:00, 18:00, 21:00
    for hour in (9, 12, 15, 18, 21):
        scheduler.add_job(
            utility_reminder, CronTrigger(day=1, hour=hour, minute=0, timezone=tz),
            args=[bot], id=f"utility_reminder_{hour}",
        )

    # Напоминания о задачах — 09:00
    scheduler.add_job(
        task_reminders, CronTrigger(hour=9, minute=0, timezone=tz),
        args=[bot], id="task_reminders",
    )

    # Гарантии — 10:00
    scheduler.add_job(
        warranty_reminders, CronTrigger(hour=10, minute=0, timezone=tz),
        args=[bot], id="warranty_reminders",
    )

    scheduler.start()
    logger.info("Планировщик запущен")
