"""Salary calculation service."""

import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.models import Salary
from bot.services.settings_service import get_float_setting


async def calculate_admin_salary(
    session: AsyncSession,
    points: int,
    langame_cash: float = 0,
) -> dict:
    """Calculate admin salary based on formula:
    ЗП = Ставка_смены + (Баллы × Цена_балла) − LanGame_Нал
    """
    shift_rate = await get_float_setting(session, "shift_rate")
    point_value = await get_float_setting(session, "point_value")

    bonus = points * point_value
    total = shift_rate + bonus - langame_cash

    return {
        "shift_rate": shift_rate,
        "points": points,
        "point_value": point_value,
        "bonus": bonus,
        "langame_cash": langame_cash,
        "total": total,
    }


async def record_admin_salary(
    session: AsyncSession,
    date: datetime.date,
    shift: str,
    employee_name: str,
    points: int,
    langame_cash: float,
    created_by: int,
    comment: str = "",
) -> Salary:
    """Record an admin salary entry."""
    calc = await calculate_admin_salary(session, points, langame_cash)

    salary = Salary(
        date=datetime.datetime.combine(date, datetime.time()),
        shift=shift,
        employee_name=employee_name,
        employee_type="admin",
        base_rate=calc["shift_rate"],
        points=points,
        point_value=calc["point_value"],
        langame_cash=langame_cash,
        total=calc["total"],
        comment=comment,
        created_by=created_by,
    )
    session.add(salary)
    await session.commit()
    return salary


async def calculate_cleaner_salary(
    session: AsyncSession,
    days_count: int,
) -> dict:
    """Calculate cleaner salary: rate × days."""
    cleaner_rate = await get_float_setting(session, "cleaner_rate")
    total = cleaner_rate * days_count

    return {
        "cleaner_rate": cleaner_rate,
        "days_count": days_count,
        "total": total,
    }


async def record_cleaner_salary(
    session: AsyncSession,
    date: datetime.date,
    employee_name: str,
    days_count: int,
    created_by: int,
    comment: str = "",
) -> Salary:
    """Record a cleaner salary entry."""
    calc = await calculate_cleaner_salary(session, days_count)

    salary = Salary(
        date=datetime.datetime.combine(date, datetime.time()),
        employee_name=employee_name,
        employee_type="cleaner",
        base_rate=calc["cleaner_rate"],
        days_count=days_count,
        total=calc["total"],
        comment=comment,
        created_by=created_by,
    )
    session.add(salary)
    await session.commit()
    return salary


async def get_month_salaries(
    session: AsyncSession, year: int, month: int
) -> list[Salary]:
    """Get all salary records for a month."""
    start = datetime.datetime(year, month, 1)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1)
    else:
        end = datetime.datetime(year, month + 1, 1)

    result = await session.execute(
        select(Salary)
        .where(and_(Salary.date >= start, Salary.date < end))
        .order_by(Salary.date)
    )
    return list(result.scalars().all())
