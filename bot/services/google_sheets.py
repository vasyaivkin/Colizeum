"""Service to read admin Google Sheets (shifts data)."""

import logging
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from config import settings
from bot.utils.dates import get_sheet_name, today_msk

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_client: gspread.Client | None = None


def get_client() -> gspread.Client:
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(
            settings.google_credentials_file, scopes=SCOPES
        )
        _client = gspread.authorize(creds)
    return _client


def get_admin_sheet(sheet_name: str | None = None) -> gspread.Worksheet:
    """Get the admin worksheet for the given month (default: current)."""
    client = get_client()
    spreadsheet = client.open_by_key(settings.admin_spreadsheet_id)
    name = sheet_name or get_sheet_name()
    return spreadsheet.worksheet(name)


def parse_number(value: str) -> float:
    """Parse a number from cell, handling Russian formatting."""
    if not value or value.strip() == "" or value.strip() == "-":
        return 0.0
    cleaned = value.strip().replace("\u00a0", "").replace(" ", "").replace(",", ".")
    cleaned = cleaned.replace("\u20bd", "").replace("₽", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def get_shift_data(target_date=None, shift: str = "day") -> dict[str, Any] | None:
    """
    Read shift data from admin sheet.
    Each date has 2 rows: row 1 = day shift, row 2 = night shift.
    shift: 'day' or 'night'
    Returns dict with all fields or None if no data.
    """
    if target_date is None:
        target_date = today_msk()

    try:
        ws = get_admin_sheet()
        all_values = ws.get_all_values()
    except Exception as e:
        logger.error(f"Error reading admin sheet: {e}")
        return None

    # Find rows for target date
    date_str_formats = [
        target_date.strftime("%d.%m.%Y"),
        target_date.strftime("%d.%m.%y"),
        target_date.strftime("%-d.%m.%Y"),
        target_date.strftime("%-d.%m.%y"),
        str(target_date.day),
    ]

    date_rows = []
    for i, row in enumerate(all_values):
        if not row:
            continue
        cell_a = str(row[0]).strip()
        for fmt in date_str_formats:
            if cell_a == fmt or cell_a.startswith(fmt):
                date_rows.append(i)
                break

    if not date_rows:
        return None

    # Day shift = first row, Night shift = second row
    row_idx = 0 if shift == "day" else 1
    if row_idx >= len(date_rows):
        # If only one row, try to determine from context
        if len(date_rows) == 1:
            row_idx = 0
        else:
            return None

    row = all_values[date_rows[row_idx]]

    # Ensure row has enough columns (A through N = 14 columns, index 0-13)
    while len(row) < 14:
        row.append("")

    admin_name = row[1].strip() if row[1] else ""
    if not admin_name:
        return None  # No admin = no data

    data = {
        "date": target_date,
        "shift": shift,
        "admin": admin_name,
        "extra_admin": row[2].strip() if row[2] else "",
        "langame_cash": parse_number(row[3]),        # D
        "card": parse_number(row[4]),                 # E - Безнал
        "sbp": parse_number(row[5]),                  # F - СБП
        "bar": parse_number(row[6]),                  # G - Бар
        "terminal_cash": parse_number(row[7]),        # H - Терминал Нал
        "langame_total": parse_number(row[8]),        # I
        "check_total": parse_number(row[9]),          # J
        "discrepancy": parse_number(row[10]),         # K
        "daily_total": parse_number(row[11]),         # L
        "compensation": parse_number(row[12]),        # M
        "comment": row[13].strip() if row[13] else "",  # N
    }

    # Calculate P&L revenue
    data["revenue_pnl"] = (
        data["langame_cash"] + data["card"] + data["sbp"] + data["terminal_cash"]
    )

    return data


def get_daily_data(target_date=None) -> dict[str, Any]:
    """Get both shifts for a date."""
    if target_date is None:
        target_date = today_msk()

    day = get_shift_data(target_date, "day")
    night = get_shift_data(target_date, "night")

    return {
        "date": target_date,
        "day": day,
        "night": night,
    }
