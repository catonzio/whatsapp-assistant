"""Sender whitelist — requirements.md §2: only the two authorized phone
numbers (the `users` table) may talk to the bot. Checked as early as possible
in the handler so an unauthorized sender never reaches transcription/LLM
calls (both cost money, see requirements.md §6).
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from whatsapp_assistant.database.models.user import User

logger = logging.getLogger("whatsapp-assistant")


class PhoneWhitelist:
    """Checks an inbound WhatsApp sender against the `users` table."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    async def is_authorized(self, phone_number: str) -> bool:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(User.id).where(User.phone_number == phone_number)
            )
            return result.scalar_one_or_none() is not None
