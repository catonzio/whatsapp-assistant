"""Framework-agnostic chat abstraction, see docs/architecture.md §3.

Only `send_async` is truly abstract. `send_sync` and `send_stream_async`
have working defaults here, overridable by concrete subclasses that can do
better (e.g. real SSE streaming). `reset_session` is abstract too: unlike
sync/streaming, "forgetting" history is framework-specific and can't be
derived generically from `send_async` — every subclass must implement it
so the "cancella la cronologia" feature actually works end to end.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from .schemas import ChatMessage


class ChatService(ABC):
    """Framework-agnostic entry point used by every interface (webhook, CLI, ...).

    Concrete subclasses (one per agent framework) confine all framework-native
    types/conversions internally — nothing framework-specific ever leaks to
    callers.
    """

    @abstractmethod
    async def send_async(self, message: ChatMessage) -> str:
        """Send a message and return the complete agent response."""

    @abstractmethod
    async def reset_session(self, user_id: str) -> None:
        """Discard the ongoing conversation history for this user.

        Lets the user start fresh on purpose (avoids burning tokens / letting
        quality degrade on an ever-growing session) — see docs/architecture.md.
        The mechanism to *trigger* this (a keyword, a WhatsApp quick reply, ...)
        is a handler-level concern, not decided yet (open point).
        """

    def send_sync(self, message: ChatMessage) -> str:
        """Convenience wrapper for standalone scripts/maintenance tools only.

        Never call this from the webhook or the CLI: both already run inside
        an active asyncio event loop, where `asyncio.run()` raises RuntimeError.
        """
        import asyncio

        return asyncio.run(self.send_async(message))

    async def send_stream_async(self, message: ChatMessage) -> AsyncIterator[str]:
        """Default: fake streaming, a single chunk with the full response.

        Overridable by subclasses that support real incremental streaming
        (e.g. ADK's SSE mode).
        """
        yield await self.send_async(message)
