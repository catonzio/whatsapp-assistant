"""ADK-backed concrete ChatService.

Confines every ADK/google-genai type conversion here — no `google.genai.types`
or ADK-specific object ever leaks to callers (webhook, handler, CLI).
"""

import logging

from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from whatsapp_assistant.agents.placeholder_agent import root_agent
from whatsapp_assistant.config import Settings
from whatsapp_assistant.services.chat_service import ChatMessage, ChatService

logger = logging.getLogger("whatsapp-assistant")

APP_NAME = "whatsapp_assistant"


def build_runner(settings: Settings) -> Runner:
    """Build the ADK Runner backed by the dedicated `agent_sessions` database.

    TEMPORARY: wraps `placeholder_agent.root_agent`. Will be replaced once the
    real domain agents are designed (docs/architecture.md §7, point 2).
    """
    session_service = DatabaseSessionService(
        db_url=settings.agent_sessions_database_url
    )
    return Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
    )


class ADKChatService(ChatService):
    """Wraps a Google ADK `Runner`. One continuous session per user_id."""

    def __init__(self, runner: Runner):
        self._runner = runner

    @staticmethod
    def _build_content(message: ChatMessage) -> types.Content:
        parts: list[types.Part] = []
        if message.text:
            parts.append(types.Part(text=message.text))
        for attachment in message.attachments:
            parts.append(
                types.Part(
                    inline_data=types.Blob(
                        data=attachment.data, mime_type=attachment.mime_type
                    )
                )
            )
        return types.Content(role="user", parts=parts)

    async def _get_or_create_session(self, user_id: str, session_id: str):
        session = await self._runner.session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        if session:
            return session
        return await self._runner.session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    async def send_async(self, message: ChatMessage) -> str:
        session_id = message.session_id or message.user_id
        await self._get_or_create_session(message.user_id, session_id)
        content = self._build_content(message)

        response_parts: list[str] = []
        async for event in self._runner.run_async(
            user_id=message.user_id,
            session_id=session_id,
            new_message=content,
        ):
            if (
                not event.is_final_response()
                or not event.content
                or not event.content.parts
            ):
                continue
            for part in event.content.parts:
                if part.text:
                    response_parts.append(part.text)
        return "".join(response_parts)

    async def reset_session(self, user_id: str) -> None:
        session_id = user_id
        session = await self._runner.session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        if session:
            await self._runner.session_service.delete_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
            logger.info(f"Reset session for user {user_id}")
