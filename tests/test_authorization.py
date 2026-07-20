import pytest

from db_utils import make_sqlite_sessionmaker
from whatsapp_assistant.database.models.user import User
from whatsapp_assistant.services.whatsapp.authorization import PhoneWhitelist


@pytest.fixture
async def whitelist() -> PhoneWhitelist:
    sessionmaker = await make_sqlite_sessionmaker(User.__table__)
    async with sessionmaker() as session:
        session.add(User(phone_number="393331112222", display_name="Alice"))
        await session.commit()
    return PhoneWhitelist(sessionmaker)


async def test_authorized_number_is_recognized(whitelist: PhoneWhitelist):
    assert await whitelist.is_authorized("393331112222") is True


async def test_unknown_number_is_rejected(whitelist: PhoneWhitelist):
    assert await whitelist.is_authorized("393339998877") is False
