import datetime
from zoneinfo import ZoneInfo

from config import settings

MONTHS_RU = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}

MONTHS_RU_GENITIVE = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

MONTH_NAMES_TO_NUM = {}
for num, name in MONTHS_RU.items():
    MONTH_NAMES_TO_NUM[name.lower()] = num
    # short forms
    MONTH_NAMES_TO_NUM[name[:3].lower()] = num
# also add common short names
_extras = {
    "янв": 1, "фев": 2, "мар": 3, "апр": 4, "мая": 5, "июн": 6,
    "июл": 7, "авг": 8, "сен": 9, "окт": 10, "ноя": 11, "дек": 12,
}
MONTH_NAMES_TO_NUM.update(_extras)


def now_msk() -> datetime.datetime:
    return datetime.datetime.now(ZoneInfo(settings.timezone))


def today_msk() -> datetime.date:
    return now_msk().date()


def get_sheet_name(dt: datetime.date | None = None) -> str:
    """Get sheet name like 'Апрель 26' for current month."""
    if dt is None:
        dt = today_msk()
    month_name = MONTHS_RU[dt.month]
    year_short = str(dt.year)[-2:]
    return f"{month_name} {year_short}"


def parse_month_name(text: str) -> int | None:
    """Parse Russian month name to number."""
    return MONTH_NAMES_TO_NUM.get(text.strip().lower())


def format_date(dt: datetime.date) -> str:
    return dt.strftime("%d.%m.%Y")


def format_date_short(dt: datetime.date) -> str:
    return dt.strftime("%d.%m")


def format_money(amount: float) -> str:
    if amount == int(amount):
        return f"{int(amount):,}".replace(",", " ") + " ₽"
    return f"{amount:,.2f}".replace(",", " ") + " ₽"
