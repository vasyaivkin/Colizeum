"""Service for writing to the management Google Sheets."""

import logging
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from config import settings
from bot.utils.dates import format_date, format_money

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_NAMES = [
    "Расход клуб",
    "ЗП + Баллы",
    "Касса",
    "Чеки",
    "Коммуналка",
    "Оборудование",
    "ПНЛ",
    "Задачи",
    "Сводный месяц",
]

SHEET_HEADERS = {
    "Расход клуб": [
        "Дата", "Смена", "LanGame Нал", "Безнал", "СБП", "Бар",
        "Терминал Нал", "Поступления прочие",
        "Барная продукция", "Зарплата", "Постоянные", "Прочие", "Коммуналка",
        "Касса", "Несхождение",
    ],
    "ЗП + Баллы": [
        "Дата", "Смена", "Сотрудник", "Тип", "Ставка", "Балл",
        "Цена балла", "LanGame Нал", "ЗП итого", "Комментарий",
    ],
    "Касса": [
        "Дата", "Тип операции", "Сумма", "Комментарий", "Остаток",
    ],
    "Чеки": [
        "Дата", "Категория", "Сумма", "Тип", "Комментарий", "Чек",
    ],
    "Коммуналка": [
        "Дата", "Т1 показания", "Т2 показания",
        "Т1 кВт·ч", "Т2 кВт·ч",
        "Т1 тариф", "Т2 тариф",
        "Т1 сумма", "Т2 сумма",
        "Итого", "Чек",
    ],
    "Оборудование": [
        "Наименование", "Статус", "Дата", "ПК/Место", "Стоимость",
        "Магазин", "Гарантия до", "Серийный", "Чек", "Описание",
    ],
    "ПНЛ": [
        "Месяц", "Выручка", "Расходы", "ЗП", "Коммуналка", "Прибыль",
    ],
    "Задачи": [
        "ID", "Описание", "Приоритет", "Срок", "Статус",
        "Создатель", "Исполнитель", "Комментарий", "Создано",
    ],
    "Сводный месяц": [
        "Месяц", "Выручка", "Бар", "Расходы", "ЗП",
        "Коммуналка", "Прибыль", "Касса",
    ],
}

_client: gspread.Client | None = None


def get_client() -> gspread.Client:
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(
            settings.google_credentials_file, scopes=SCOPES
        )
        _client = gspread.authorize(creds)
    return _client


def create_management_spreadsheet(title: str = "COLIZEUM — Управление") -> str:
    """Create the management spreadsheet with all required sheets.
    Returns the spreadsheet ID.
    """
    client = get_client()
    spreadsheet = client.create(title)

    # Rename default sheet to first name
    default_sheet = spreadsheet.sheet1
    default_sheet.update_title(SHEET_NAMES[0])
    default_sheet.append_row(SHEET_HEADERS[SHEET_NAMES[0]])

    # Create remaining sheets
    for name in SHEET_NAMES[1:]:
        ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
        if name in SHEET_HEADERS:
            ws.append_row(SHEET_HEADERS[name])

    spreadsheet_id = spreadsheet.id
    logger.info(f"Created management spreadsheet: {spreadsheet_id}")
    return spreadsheet_id


def get_management_spreadsheet() -> gspread.Spreadsheet:
    """Get the management spreadsheet."""
    client = get_client()
    sid = settings.management_spreadsheet_id
    if not sid:
        raise ValueError("Management spreadsheet not configured")
    return client.open_by_key(sid)


def get_management_sheet(sheet_name: str) -> gspread.Worksheet:
    """Get a specific sheet from management spreadsheet."""
    spreadsheet = get_management_spreadsheet()
    return spreadsheet.worksheet(sheet_name)


def append_expense_row(
    date: str, category: str, amount: float, payment_type: str,
    comment: str, receipt_link: str = "",
):
    """Append a row to the Чеки sheet."""
    try:
        ws = get_management_sheet("Чеки")
        receipt_cell = ""
        if receipt_link:
            short_date = date.split(".")[0] + "." + date.split(".")[1] if "." in date else date
            receipt_cell = f'=HYPERLINK("{receipt_link}", "📎 Чек от {short_date}")'

        ws.append_row([date, category, amount, payment_type, comment, receipt_cell],
                      value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Error writing expense to Sheets: {e}")


def append_cash_row(date: str, op_type: str, amount: float, comment: str, balance: float):
    """Append a row to the Касса sheet."""
    try:
        ws = get_management_sheet("Касса")
        ws.append_row([date, op_type, amount, comment, balance],
                      value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Error writing cash op to Sheets: {e}")


def append_salary_row(row_data: list):
    """Append a row to the ЗП + Баллы sheet."""
    try:
        ws = get_management_sheet("ЗП + Баллы")
        ws.append_row(row_data, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Error writing salary to Sheets: {e}")


def append_utility_row(row_data: list):
    """Append a row to the Коммуналка sheet."""
    try:
        ws = get_management_sheet("Коммуналка")
        ws.append_row(row_data, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Error writing utility to Sheets: {e}")


def append_equipment_row(row_data: list):
    """Append a row to the Оборудование sheet."""
    try:
        ws = get_management_sheet("Оборудование")
        ws.append_row(row_data, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Error writing equipment to Sheets: {e}")


def append_task_row(row_data: list):
    """Append a row to the Задачи sheet."""
    try:
        ws = get_management_sheet("Задачи")
        ws.append_row(row_data, value_input_option="USER_ENTERED")
    except Exception as e:
        logger.error(f"Error writing task to Sheets: {e}")


def update_task_row(task_id: int, status: str, comment: str = ""):
    """Update task status in Sheets."""
    try:
        ws = get_management_sheet("Задачи")
        cell = ws.find(str(task_id), in_column=1)
        if cell:
            ws.update_cell(cell.row, 5, status)
            if comment:
                ws.update_cell(cell.row, 8, comment)
    except Exception as e:
        logger.error(f"Error updating task in Sheets: {e}")
