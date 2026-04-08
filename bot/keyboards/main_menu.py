"""Main menu and common keyboards."""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)


def main_menu_kb() -> ReplyKeyboardMarkup:
    """Main reply keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="\U0001f4ca \u041e\u0442\u0447\u0451\u0442"),
                KeyboardButton(text="\U0001f4b0 \u0420\u0430\u0441\u0445\u043e\u0434"),
            ],
            [
                KeyboardButton(text="\U0001f4b5 \u041a\u0430\u0441\u0441\u0430"),
                KeyboardButton(text="\U0001f4b3 \u041f\u043e\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u0435"),
            ],
            [
                KeyboardButton(text="\U0001f4b4 \u0417\u041f"),
                KeyboardButton(text="\U0001f4a1 \u041a\u043e\u043c\u043c\u0443\u043d\u0430\u043b\u043a\u0430"),
            ],
            [
                KeyboardButton(text="\U0001f5a5 \u041e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u0435"),
                KeyboardButton(text="\U0001f4cb \u0417\u0430\u0434\u0430\u0447\u0438"),
            ],
            [
                KeyboardButton(text="\u2699\ufe0f \u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438"),
                KeyboardButton(text="\u2753 \u041f\u043e\u043c\u043e\u0449\u044c"),
            ],
        ],
        resize_keyboard=True,
    )


def expense_category_kb() -> InlineKeyboardMarkup:
    """Expense category selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4e6 \u0411\u0430\u0440\u043d\u0430\u044f", callback_data="exp_cat:bar")],
        [InlineKeyboardButton(text="\U0001f464 \u0417\u0430\u0440\u043f\u043b\u0430\u0442\u0430", callback_data="exp_cat:salary")],
        [InlineKeyboardButton(text="\U0001f3e2 \u041f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u044b\u0435", callback_data="exp_cat:fixed")],
        [InlineKeyboardButton(text="\U0001f4ce \u041f\u0440\u043e\u0447\u0438\u0435", callback_data="exp_cat:other")],
        [InlineKeyboardButton(text="\U0001f4a1 \u041a\u043e\u043c\u043c\u0443\u043d\u0430\u043b\u043a\u0430", callback_data="exp_cat:utility")],
    ])


CATEGORY_NAMES = {
    "bar": "\u0411\u0430\u0440\u043d\u0430\u044f \u043f\u0440\u043e\u0434\u0443\u043a\u0446\u0438\u044f",
    "salary": "\u0417\u0430\u0440\u043f\u043b\u0430\u0442\u0430",
    "fixed": "\u041f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u044b\u0435 \u0440\u0430\u0441\u0445\u043e\u0434\u044b",
    "other": "\u041f\u0440\u043e\u0447\u0438\u0435 \u0440\u0430\u0441\u0445\u043e\u0434\u044b",
    "utility": "\u041a\u043e\u043c\u043c\u0443\u043d\u0430\u043b\u043a\u0430",
}


def payment_type_kb() -> InlineKeyboardMarkup:
    """Payment type selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f4b5 \u041d\u0430\u043b", callback_data="pay:cash"),
            InlineKeyboardButton(text="\U0001f4b3 \u0411\u0435\u0437\u043d\u0430\u043b", callback_data="pay:card"),
        ],
    ])


def from_cash_kb() -> InlineKeyboardMarkup:
    """From cash register?"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="\u2705 \u0414\u0430 \u2014 \u0432\u044b\u0447\u0435\u0441\u0442\u044c \u0438\u0437 \u043a\u0430\u0441\u0441\u044b",
                callback_data="from_cash:yes",
            ),
        ],
        [
            InlineKeyboardButton(text="\u041d\u0435\u0442", callback_data="from_cash:no"),
        ],
    ])


def receipt_ask_kb() -> InlineKeyboardMarkup:
    """Attach receipt?"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001f4f8 \u041f\u0440\u0438\u043a\u0440\u0435\u043f\u0438\u0442\u044c \u0444\u043e\u0442\u043e", callback_data="receipt:yes"),
            InlineKeyboardButton(text="\u041f\u0440\u043e\u043f\u0443\u0441\u0442\u0438\u0442\u044c", callback_data="receipt:no"),
        ],
    ])


def confirm_or_manual_kb() -> InlineKeyboardMarkup:
    """Confirm calculated amount or enter manually."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="\u0412\u0435\u0440\u043d\u043e \u2713", callback_data="utility_confirm:yes"),
            InlineKeyboardButton(text="\u0412\u0432\u0435\u0441\u0442\u0438 \u0432\u0440\u0443\u0447\u043d\u0443\u044e", callback_data="utility_confirm:manual"),
        ],
    ])


def points_kb() -> InlineKeyboardMarkup:
    """Points selection -3..+3."""
    buttons = []
    row = []
    for p in range(-3, 4):
        label = f"+{p}" if p > 0 else str(p)
        row.append(InlineKeyboardButton(text=f"[{label}]", callback_data=f"points:{p}"))
    buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def task_priority_kb() -> InlineKeyboardMarkup:
    """Task priority selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f534 \u0421\u0440\u043e\u0447\u043d\u043e", callback_data="priority:urgent")],
        [InlineKeyboardButton(text="\U0001f7e1 \u041e\u0431\u044b\u0447\u043d\u0430\u044f", callback_data="priority:normal")],
        [InlineKeyboardButton(text="\u26aa \u041a\u043e\u0433\u0434\u0430 \u0431\u0443\u0434\u0435\u0442 \u0432\u0440\u0435\u043c\u044f", callback_data="priority:low")],
    ])


def task_actions_kb(task_id: int, is_creator: bool = False) -> InlineKeyboardMarkup:
    """Task action buttons."""
    buttons = [
        [InlineKeyboardButton(text="\u2705 \u0412\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043e", callback_data=f"task_done:{task_id}")],
        [InlineKeyboardButton(text="\U0001f4ac \u041a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439", callback_data=f"task_comment:{task_id}")],
        [InlineKeyboardButton(text="\u270f \u0420\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c", callback_data=f"task_edit:{task_id}")],
    ]
    if is_creator:
        buttons.append([
            InlineKeyboardButton(text="\U0001f5d1 \u0423\u0434\u0430\u043b\u0438\u0442\u044c", callback_data=f"task_delete:{task_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def income_destination_kb() -> InlineKeyboardMarkup:
    """Income destination selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4b5 \u0412 \u043a\u0430\u0441\u0441\u0443", callback_data="dest:cash")],
        [InlineKeyboardButton(text="\U0001f3e6 \u041d\u0430 \u0441\u0447\u0451\u0442", callback_data="dest:account")],
        [InlineKeyboardButton(text="\U0001f4e4 \u041d\u0430 \u0440\u0430\u0441\u0445\u043e\u0434\u044b", callback_data="dest:expenses")],
    ])


def salary_type_kb() -> InlineKeyboardMarkup:
    """Salary type selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f464 \u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440", callback_data="sal_type:admin")],
        [InlineKeyboardButton(text="\U0001f9f9 \u0423\u0431\u043e\u0440\u0449\u0438\u0446\u0430", callback_data="sal_type:cleaner")],
    ])


def equipment_menu_kb() -> InlineKeyboardMarkup:
    """Equipment menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f534 \u0421\u043b\u043e\u043c\u0430\u043b\u043e\u0441\u044c", callback_data="equip:break")],
        [InlineKeyboardButton(text="\U0001f527 \u0420\u0435\u043c\u043e\u043d\u0442", callback_data="equip:repair")],
        [InlineKeyboardButton(text="\U0001f7e2 \u041a\u0443\u043f\u043b\u0435\u043d\u043e", callback_data="equip:purchase")],
        [InlineKeyboardButton(text="\U0001f5d1 \u0421\u043f\u0438\u0441\u0430\u043d\u0438\u0435", callback_data="equip:decommission")],
        [InlineKeyboardButton(text="\U0001f4cb \u0418\u043d\u0432\u0435\u043d\u0442\u0430\u0440\u0438\u0437\u0430\u0446\u0438\u044f", callback_data="equip:inventory")],
        [InlineKeyboardButton(text="\U0001f4c4 \u0412\u0441\u0451 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u0435", callback_data="equip:list")],
        [InlineKeyboardButton(text="\u26a0\ufe0f \u041f\u043e\u043b\u043e\u043c\u043a\u0438", callback_data="equip:broken")],
        [InlineKeyboardButton(text="\U0001f6e1 \u0413\u0430\u0440\u0430\u043d\u0442\u0438\u0438", callback_data="equip:warranties")],
    ])


def settings_menu_kb() -> InlineKeyboardMarkup:
    """Settings menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4b0 \u0421\u0442\u0430\u0432\u043a\u0430 \u0441\u043c\u0435\u043d\u044b", callback_data="set:shift_rate")],
        [InlineKeyboardButton(text="\u2b50 \u0426\u0435\u043d\u0430 \u0431\u0430\u043b\u043b\u0430", callback_data="set:point_value")],
        [InlineKeyboardButton(text="\U0001f9f9 \u0423\u0431\u043e\u0440\u0449\u0438\u0446\u0430", callback_data="set:cleaner_rate")],
        [InlineKeyboardButton(text="\u26a1 \u0422\u0430\u0440\u0438\u0444 \u04221 (\u0434\u0435\u043d\u044c)", callback_data="set:t1_tariff")],
        [InlineKeyboardButton(text="\U0001f319 \u0422\u0430\u0440\u0438\u0444 \u04222 (\u043d\u043e\u0447\u044c)", callback_data="set:t2_tariff")],
        [InlineKeyboardButton(text="\U0001f517 ID \u0442\u0430\u0431\u043b\u0438\u0446\u044b \u0430\u0434\u043c\u0438\u043d\u043e\u0432", callback_data="set:admin_spreadsheet")],
        [InlineKeyboardButton(text="\U0001f4e5 \u041f\u0440\u0438\u0433\u043b\u0430\u0441\u0438\u0442\u044c", callback_data="set:invite")],
    ])


SETTING_NAMES = {
    "shift_rate": "\u0421\u0442\u0430\u0432\u043a\u0430 \u0437\u0430 \u0441\u043c\u0435\u043d\u0443",
    "point_value": "\u0426\u0435\u043d\u0430 \u0431\u0430\u043b\u043b\u0430",
    "cleaner_rate": "\u0421\u0442\u0430\u0432\u043a\u0430 \u0443\u0431\u043e\u0440\u0449\u0438\u0446\u044b",
    "t1_tariff": "\u0422\u0430\u0440\u0438\u0444 \u04221 (\u0434\u0435\u043d\u044c)",
    "t2_tariff": "\u0422\u0430\u0440\u0438\u0444 \u04222 (\u043d\u043e\u0447\u044c)",
}


def report_period_kb() -> InlineKeyboardMarkup:
    """Report period selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\U0001f4c5 \u0421\u0435\u0433\u043e\u0434\u043d\u044f", callback_data="report:today")],
        [InlineKeyboardButton(text="\U0001f4c6 \u041d\u0435\u0434\u0435\u043b\u044f", callback_data="report:week")],
        [InlineKeyboardButton(text="\U0001f4c5 \u041c\u0435\u0441\u044f\u0446", callback_data="report:month")],
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    """Cancel button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="\u274c \u041e\u0442\u043c\u0435\u043d\u0430", callback_data="cancel")],
    ])
