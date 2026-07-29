"""ADK-backed concrete ChatService.

Confines every ADK/google-genai type conversion here — no `google.genai.types`
or ADK-specific object ever leaks to callers (webhook, handler, CLI).
"""

import asyncio
import logging

from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from whatsapp_assistant.agents.orchestrator_agent import build_root_agent
from whatsapp_assistant.configs.settings import Settings, get_settings
from ..chat_service import ChatService
from ..schemas import ChatMessage

logger = logging.getLogger("whatsapp-assistant")

APP_NAME = "whatsapp_assistant"


def build_runner(settings: Settings) -> Runner:
    """Build the ADK Runner backed by the dedicated `agent_sessions` database.

    Builds the root agent here (not at import time, see
    orchestrator_agent.build_root_agent's docstring) so that constructing a
    domain agent's tools — which can raise if e.g. Google Places is selected
    without an API key — only fails when a real Runner is actually needed.
    """
    session_service = DatabaseSessionService(
        db_url=settings.agent_sessions_database_url
    )
    return Runner(
        app_name=APP_NAME,
        agent=build_root_agent(
            orchestrator_model=settings.gemini_model_orchestrator,
            subagents_model=settings.gemini_model_subagent,
        ),
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
    )


class ADKChatService(ChatService):
    """Wraps a Google ADK `Runner`. One continuous session per user_id.

    Serializes `send_async`/`reset_session` per user_id with an in-memory
    asyncio.Lock: without it, two messages arriving close together for the
    same user (e.g. a voice note immediately followed by a text) can run
    `_get_or_create_session`/`run_async` concurrently against the same ADK
    session, racing on session creation and interleaving the Runner's
    session-state updates. `_locks` grows one entry per distinct user_id ever
    seen and is never evicted — fine at this app's scale (two users, per
    requirements.md §2); would need eviction for a system with unbounded users.
    """

    def __init__(self, runner: Runner | None = None):
        self._runner = runner or build_runner(get_settings())
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, user_id: str) -> asyncio.Lock:
        # dict.setdefault has no `await` inside it, so this can't race even
        # though asyncio is single-threaded and cooperative.
        return self._locks.setdefault(user_id, asyncio.Lock())

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
        new_session = await self._runner.session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        return new_session

    async def send_async(self, message: ChatMessage) -> str:
        session_id = message.session_id or message.user_id
        async with self._lock_for(message.user_id):
            await self._get_or_create_session(message.user_id, session_id)
            content = self._build_content(message)

            response_parts: list[str] = []
            async for event in self._runner.run_async(
                user_id=message.user_id,
                session_id=session_id,
                new_message=content,
            ):
                # A single_turn sub-agent delegation (orchestrator_agent.py)
                # runs inline in this session, so its own final-response event
                # is also visible here alongside the orchestrator's — without
                # the author check we'd concatenate both and duplicate the
                # sub-agent's answer with the orchestrator's rephrasing of it.
                runner_agent = self._runner.agent
                if not runner_agent:
                    raise RuntimeError("Runner has no agent")

                if (
                    event.author != runner_agent.name
                    or not event.is_final_response()
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
        async with self._lock_for(user_id):
            session = await self._runner.session_service.get_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )
            if session:
                await self._runner.session_service.delete_session(
                    app_name=APP_NAME, user_id=user_id, session_id=session_id
                )
                logger.info(f"Reset session for user {user_id}")
