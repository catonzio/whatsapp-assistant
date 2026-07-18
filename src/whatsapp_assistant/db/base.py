from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models of the application database.

    Only for domain data (items, categories, reminders, lists, users).
    ADK's DatabaseSessionService manages its own schema in a separate
    database (agent_sessions) and is NOT modeled here.
    """
