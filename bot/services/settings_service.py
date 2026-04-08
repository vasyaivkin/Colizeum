"""Service for managing bot settings stored in DB."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.models import Setting

# Default settings
DEFAULTS = {
    "shift_rate": "2500",
    "point_value": "300",
    "cleaner_rate": "800",
    "t1_tariff": "4.50",
    "t2_tariff": "2.20",
    "chat_id": "",
    "management_spreadsheet_id": "",
}


async def get_setting(session: AsyncSession, key: str) -> str:
    """Get a setting value, returning default if not set."""
    result = await session.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        return setting.value
    return DEFAULTS.get(key, "")


async def set_setting(session: AsyncSession, key: str, value: str):
    """Set or update a setting."""
    result = await session.execute(select(Setting).where(Setting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        session.add(Setting(key=key, value=value))
    await session.commit()


async def get_float_setting(session: AsyncSession, key: str) -> float:
    val = await get_setting(session, key)
    try:
        return float(val)
    except (ValueError, TypeError):
        return float(DEFAULTS.get(key, "0"))


async def get_all_settings(session: AsyncSession) -> dict[str, str]:
    """Get all settings as dict."""
    result = await session.execute(select(Setting))
    settings_list = result.scalars().all()
    data = dict(DEFAULTS)
    for s in settings_list:
        data[s.key] = s.value
    return data
