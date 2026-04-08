"""Handlers for /start and /invite commands."""

import secrets
import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy import select, func

from bot.models.database import async_session
from bot.models.models import User, Invite
from bot.keyboards.main_menu import main_menu_kb
from bot.services.settings_service import set_setting, get_setting
from bot.services.management_sheets import create_management_spreadsheet
from config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start — registration or invite acceptance."""
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    invite_token = args[1] if len(args) > 1 else None

    async with async_session() as session:
        # Проверяем, зарегистрирован ли пользователь
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            await message.answer(
                f"С возвращением, {existing.first_name}!\n"
                f"Роль: {_role_name(existing.role)}",
                reply_markup=main_menu_kb(),
            )
            return

        # Подсчитываем существующих пользователей
        count_result = await session.execute(
            select(func.count()).select_from(User)
        )
        user_count = count_result.scalar()

        if user_count == 0:
            # Первый пользователь — собственник
            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or "Собственник",
                role="owner",
            )
            session.add(user)
            await session.commit()

            # Сохраняем chat_id для отчётов
            await set_setting(session, "chat_id", str(message.chat.id))

            # Создаём управленческую таблицу если не настроена
            if not settings.management_spreadsheet_id:
                try:
                    spreadsheet_id = create_management_spreadsheet()
                    await set_setting(session, "management_spreadsheet_id", spreadsheet_id)
                    settings.management_spreadsheet_id = spreadsheet_id
                    await message.answer(
                        f"📊 Управленческая таблица создана автоматически.\n"
                        f"ID: {spreadsheet_id}"
                    )
                except Exception as e:
                    await message.answer(
                        f"⚠ Не удалось создать таблицу автоматически: {e}\n"
                        f"Можно настроить вручную через /настройки"
                    )

            await message.answer(
                f"🏛 Добро пожаловать в COLIZEUM!\n\n"
                f"Вы зарегистрированы как Собственник.\n"
                f"Используйте /invite чтобы пригласить управляющего.",
                reply_markup=main_menu_kb(),
            )
            return

        if user_count >= 2 and not invite_token:
            await message.answer(
                "⛔ Бот рассчитан на двух пользователей.\n"
                "Попросите собственника или управляющего прислать ссылку-инвайт."
            )
            return

        # Регистрация по инвайту
        if invite_token:
            result = await session.execute(
                select(Invite).where(
                    Invite.token == invite_token,
                    Invite.used_by.is_(None),
                )
            )
            invite = result.scalar_one_or_none()

            if not invite:
                await message.answer("⛔ Инвайт недействителен или уже использован.")
                return

            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or "Управляющий",
                role="manager",
            )
            session.add(user)

            invite.used_by = user_id
            invite.used_at = datetime.datetime.now()
            await session.commit()

            await message.answer(
                f"✅ Добро пожаловать в COLIZEUM!\n\n"
                f"Вы зарегистрированы как Управляющий.\n"
                f"У вас полный доступ ко всем функциям.",
                reply_markup=main_menu_kb(),
            )

            # Уведомить создателя инвайта
            try:
                from aiogram import Bot
                bot = message.bot
                await bot.send_message(
                    invite.created_by,
                    f"👤 Новый пользователь присоединился: "
                    f"{message.from_user.first_name} (@{message.from_user.username})"
                )
            except Exception:
                pass

            return

        # Нет инвайта и уже есть 1 пользователь
        await message.answer(
            "⛔ Для регистрации нужна ссылка-инвайт.\n"
            "Попросите собственника: /invite"
        )


@router.message(Command("invite"))
async def cmd_invite(message: Message):
    """Создать ссылку-инвайт."""
    user_id = message.from_user.id

    async with async_session() as session:
        # Проверяем что пользователь зарегистрирован
        result = await session.execute(
            select(User).where(User.telegram_id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("⛔ Вы не зарегистрированы.")
            return

        # Генерируем токен
        token = secrets.token_urlsafe(32)
        invite = Invite(token=token, created_by=user_id)
        session.add(invite)
        await session.commit()

        bot_info = await message.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={token}"

        await message.answer(
            f"🔗 Ссылка-инвайт для второго пользователя:\n\n"
            f"{link}\n\n"
            f"Ссылка одноразовая. Отправьте её управляющему/собственнику."
        )


def _role_name(role: str) -> str:
    return {"owner": "Собственник", "manager": "Управляющий"}.get(role, role)
