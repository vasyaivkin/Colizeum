"""Report formatting utilities."""

from bot.utils.dates import format_money, format_date, format_date_short


def fmt(amount: float | None) -> str:
    """Format money amount, default to 0."""
    if amount is None:
        return format_money(0)
    return format_money(amount)


def fmt_int(amount: float | None) -> str:
    """Format as integer money."""
    if amount is None:
        return "0 ₽"
    return f"{int(amount):,}".replace(",", " ") + " ₽"


def warn_discrepancy(value: float | None) -> str:
    """Add warning emoji if value != 0."""
    if value and value != 0:
        return "  ⚠"
    return ""


def format_shift_report(
    shift_type: str,
    date_str: str,
    admin_name: str,
    langame_cash: float,
    card: float,
    sbp: float,
    terminal_cash: float,
    bar: float,
    langame_total: float,
    check_total: float,
    discrepancy: float,
    daily_total: float,
    compensation: float = 0,
    comment: str = "",
    extra_admin: str = "",
) -> str:
    """Format a shift report message."""
    shift_total = langame_cash + card + sbp + terminal_cash

    if shift_type == "day":
        emoji = "\U0001f4ca"
        header = f"{emoji} ДНЕВНАЯ СМЕНА · {date_str}"
    else:
        emoji = "\U0001f319"
        header = f"{emoji} НОЧНАЯ СМЕНА · {date_str}"

    admin_line = f"\U0001f464 Администратор: {admin_name}"
    if extra_admin:
        admin_line += f" (+ {extra_admin})"

    lines = [
        header,
        admin_line,
        "═" * 30,
        "ВЫРУЧКА (в P&L):",
        f"  LanGame Нал:       {fmt_int(langame_cash)}",
        f"  Безнал:          {fmt_int(card)}",
        f"  СБП:             {fmt_int(sbp)}",
        f"  Нал (терминал):  {fmt_int(terminal_cash)}",
        f"  Итого смена:    {fmt_int(shift_total)}",
        "",
        "СПРАВОЧНО (не в P&L):",
        f"  Бар:             {fmt_int(bar)}",
        f"  Итог по LanGame: {fmt_int(langame_total)}",
        f"  Итог по Чеку:    {fmt_int(check_total)}",
        f"  Несхождение:      {fmt_int(discrepancy)}{warn_discrepancy(discrepancy)}",
    ]

    if compensation:
        lines.append(f"  Компенсации:      {fmt_int(compensation)}")

    lines.extend([
        "",
        f"\U0001f4b5 Нал в кассу (терминал): {fmt_int(terminal_cash)}",
        f"\U0001f4cb Комментарий: {comment or '—'}",
        "═" * 30,
        f"\U0001f4c5 Общая за сутки (кол. L): {fmt_int(daily_total)}",
    ])

    return "\n".join(lines)


def format_daily_summary(
    date_str: str,
    day_data: dict | None,
    night_data: dict | None,
    expenses: dict,
    cash_balance: float,
    warnings: list[str],
) -> str:
    """Format the full daily summary report."""
    total_langame_cash = (day_data or {}).get("langame_cash", 0) + (night_data or {}).get("langame_cash", 0)
    total_card = (day_data or {}).get("card", 0) + (night_data or {}).get("card", 0)
    total_sbp = (day_data or {}).get("sbp", 0) + (night_data or {}).get("sbp", 0)
    total_terminal = (day_data or {}).get("terminal_cash", 0) + (night_data or {}).get("terminal_cash", 0)
    total_revenue = total_langame_cash + total_card + total_sbp + total_terminal
    total_bar = (day_data or {}).get("bar", 0) + (night_data or {}).get("bar", 0)

    total_expenses = sum(expenses.values())
    profit = total_revenue - total_expenses

    lines = [
        "─" * 30,
        f"\U0001f4c5 СУТОЧНЫЙ ИТОГ · {date_str}",
        "─" * 30,
        "ВЫРУЧКА ОБЕИХ СМЕН (P&L):",
        f"  LanGame Нал:         {fmt_int(total_langame_cash)}",
        f"  Безнал:           {fmt_int(total_card)}",
        f"  СБП:              {fmt_int(total_sbp)}",
        f"  Нал (терминал):    {fmt_int(total_terminal)}",
        f"  ИТОГО выручка:    {fmt_int(total_revenue)}",
        "",
        "СПРАВОЧНО (не в P&L):",
        f"  Бар за сутки:      {fmt_int(total_bar)}",
        "",
        "РАСХОДЫ (внесено вручную):",
        f"  Барная продукция:  {fmt_int(expenses.get('bar', 0))}",
        f"  Зарплата:          {fmt_int(expenses.get('salary', 0))}",
        f"  Постоянные расходы: {fmt_int(expenses.get('fixed', 0))}",
        f"  Прочие:            {fmt_int(expenses.get('other', 0))}",
        f"  Коммуналка:        {fmt_int(expenses.get('utility', 0))}",
        f"  ИТОГО расходы:     {fmt_int(total_expenses)}",
        "",
        f"\U0001f4b5 КАССА (нал терминал): {fmt_int(cash_balance)}",
        f"\U0001f4c8 ПРИБЫЛЬ (предв.): {fmt_int(profit)}",
        "═" * 30,
    ]

    for w in warnings:
        lines.append(f"❗ {w}")

    return "\n".join(lines)
