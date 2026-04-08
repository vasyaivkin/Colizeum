"""Cash register service."""

import datetime
import logging

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.models import CashOperation, Expense, Income
from bot.utils.dates import today_msk, format_money

logger = logging.getLogger(__name__)


async def get_cash_balance(session: AsyncSession) -> float:
    """Get current cash balance from last operation."""
    result = await session.execute(
        select(CashOperation)
        .order_by(desc(CashOperation.id))
        .limit(1)
    )
    last_op = result.scalar_one_or_none()
    return last_op.balance_after if last_op else 0.0


async def add_cash_operation(
    session: AsyncSession,
    operation_type: str,
    amount: float,
    comment: str = "",
    reference_id: int | None = None,
    reference_type: str | None = None,
) -> CashOperation:
    """Add a cash operation and update balance."""
    balance = await get_cash_balance(session)
    new_balance = balance + amount

    op = CashOperation(
        date=datetime.datetime.now(),
        operation_type=operation_type,
        amount=amount,
        comment=comment,
        balance_after=new_balance,
        reference_id=reference_id,
        reference_type=reference_type,
    )
    session.add(op)
    await session.commit()
    return op


async def add_terminal_cash(
    session: AsyncSession, amount: float, shift_info: str = ""
) -> CashOperation:
    """Record terminal cash income to register."""
    return await add_cash_operation(
        session,
        operation_type="terminal_cash",
        amount=amount,
        comment=f"Терминал нал: {shift_info}",
        reference_type="shift",
    )


async def add_expense_cash(
    session: AsyncSession, amount: float, expense_id: int, comment: str = ""
) -> CashOperation:
    """Record cash expense from register."""
    return await add_cash_operation(
        session,
        operation_type="expense",
        amount=-abs(amount),
        comment=comment,
        reference_id=expense_id,
        reference_type="expense",
    )


async def add_income_cash(
    session: AsyncSession, amount: float, income_id: int, comment: str = ""
) -> CashOperation:
    """Record cash income to register."""
    return await add_cash_operation(
        session,
        operation_type="income",
        amount=amount,
        comment=comment,
        reference_id=income_id,
        reference_type="income",
    )


async def get_today_operations(session: AsyncSession) -> list[CashOperation]:
    """Get all cash operations for today."""
    today = today_msk()
    start = datetime.datetime.combine(today, datetime.time.min)
    end = datetime.datetime.combine(today, datetime.time.max)

    result = await session.execute(
        select(CashOperation)
        .where(and_(CashOperation.date >= start, CashOperation.date <= end))
        .order_by(CashOperation.id)
    )
    return list(result.scalars().all())


async def get_recent_operations(session: AsyncSession, limit: int = 20) -> list[CashOperation]:
    """Get last N operations."""
    result = await session.execute(
        select(CashOperation)
        .order_by(desc(CashOperation.id))
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_month_summary(
    session: AsyncSession, year: int, month: int
) -> dict:
    """Get cash summary for a given month."""
    start = datetime.datetime(year, month, 1)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1)
    else:
        end = datetime.datetime(year, month + 1, 1)

    result = await session.execute(
        select(CashOperation)
        .where(and_(CashOperation.date >= start, CashOperation.date < end))
        .order_by(CashOperation.id)
    )
    ops = list(result.scalars().all())

    # Get opening balance (balance before first operation of month)
    opening = 0.0
    if ops:
        opening = ops[0].balance_after - ops[0].amount

    terminal_total = sum(op.amount for op in ops if op.operation_type == "terminal_cash")
    income_total = sum(op.amount for op in ops if op.operation_type == "income")
    expense_total = sum(abs(op.amount) for op in ops if op.operation_type == "expense")

    # Get expense breakdown by category
    expense_ids = [
        op.reference_id for op in ops
        if op.operation_type == "expense" and op.reference_id
    ]
    categories = {}
    if expense_ids:
        exp_result = await session.execute(
            select(Expense).where(Expense.id.in_(expense_ids))
        )
        for exp in exp_result.scalars().all():
            cat = exp.category
            categories[cat] = categories.get(cat, 0) + exp.amount

    closing = opening + terminal_total + income_total - expense_total

    return {
        "opening": opening,
        "terminal_cash": terminal_total,
        "income": income_total,
        "total_income": terminal_total + income_total,
        "expenses_by_category": categories,
        "total_expenses": expense_total,
        "closing": closing,
    }
