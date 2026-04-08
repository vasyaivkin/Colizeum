"""Authorization middleware - only registered users can use the bot."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy import select

from bot.models.database import async_session
from bot.models.models import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Check if user is registered before processing any handler."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract user from event
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            # Allow /start without auth (for registration)
            if event.text and event.text.startswith("/start"):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if user_id is None:
            return

        # Check if user is registered
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user_id, User.is_active == True)
            )
            user = result.scalar_one_or_none()

        if user is None:
            if isinstance(event, Message):
                await event.answer(
                    "\u26d4 \u0412\u044b \u043d\u0435 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b. "
                    "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 /start \u0438\u043b\u0438 \u0441\u0441\u044b\u043b\u043a\u0443-\u0438\u043d\u0432\u0430\u0439\u0442."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "\u26d4 \u0412\u044b \u043d\u0435 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b.",
                    show_alert=True,
                )
            return

        # Attach user to data for handlers
        data["db_user"] = user
        return await handler(event, data)
