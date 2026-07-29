import asyncio
from types import SimpleNamespace

from whatsapp_assistant.services.chat_service.impls.adk_chat_service import (
    APP_NAME,
    ADKChatService,
)
from whatsapp_assistant.services.chat_service.schemas import ChatMessage


class FakeSessionService:
    """Minimal stand-in for ADK's DatabaseSessionService, in-memory only."""

    def __init__(self) -> None:
        self._sessions: dict[tuple[str, str], object] = {}
        self.create_calls: list[tuple[str, str]] = []
        self.delete_calls: list[tuple[str, str]] = []

    async def get_session(self, app_name: str, user_id: str, session_id: str):
        assert app_name == APP_NAME
        return self._sessions.get((user_id, session_id))

    async def create_session(self, app_name: str, user_id: str, session_id: str):
        session = SimpleNamespace(user_id=user_id, session_id=session_id)
        self._sessions[(user_id, session_id)] = session
        self.create_calls.append((user_id, session_id))
        return session

    async def delete_session(self, app_name: str, user_id: str, session_id: str):
        self._sessions.pop((user_id, session_id), None)
        self.delete_calls.append((user_id, session_id))


ROOT_AGENT_NAME = "OrchestratorAssistant"


class FakeEvent:
    def __init__(
        self,
        text: str | None,
        final: bool = True,
        author: str = ROOT_AGENT_NAME,
    ) -> None:
        self._final = final
        self.author = author
        self.content = SimpleNamespace(parts=[SimpleNamespace(text=text)]) if text is not None else None

    def is_final_response(self) -> bool:
        return self._final


def _service(runner) -> ADKChatService:
    return ADKChatService(runner=runner)


async def test_send_async_concatenates_only_final_text_parts():
    class FakeRunner:
        def __init__(self) -> None:
            self.session_service = FakeSessionService()
            self.agent = SimpleNamespace(name=ROOT_AGENT_NAME)

        async def run_async(self, user_id, session_id, new_message):
            yield FakeEvent(None, final=False)  # intermediate event, must be ignored
            yield FakeEvent("Ciao ")
            yield FakeEvent("mondo!")

    runner = FakeRunner()
    service = _service(runner)

    result = await service.send_async(ChatMessage(user_id="u1", text="hi"))

    assert result == "Ciao mondo!"


async def test_send_async_ignores_sub_agent_final_response():
    """A single_turn sub-agent delegation (orchestrator_agent.py) runs inline
    in this session, so its own final-response event is also visible in the
    stream alongside the orchestrator's. Without filtering by author, both
    get concatenated and the sub-agent's answer is duplicated."""

    class FakeRunner:
        def __init__(self) -> None:
            self.session_service = FakeSessionService()
            self.agent = SimpleNamespace(name=ROOT_AGENT_NAME)

        async def run_async(self, user_id, session_id, new_message):
            yield FakeEvent(
                "Nella lista Spesa ci sono: petto di pollo, carne macinata",
                author="ListsTasksAgent",
            )
            yield FakeEvent(
                "Nella lista Spesa ci sono: petto di pollo, carne macinata",
                author=ROOT_AGENT_NAME,
            )

    runner = FakeRunner()
    service = _service(runner)

    result = await service.send_async(ChatMessage(user_id="u1", text="hi"))

    assert result == "Nella lista Spesa ci sono: petto di pollo, carne macinata"


async def test_send_async_creates_session_when_absent_and_reuses_it():
    class FakeRunner:
        def __init__(self) -> None:
            self.session_service = FakeSessionService()
            self.agent = SimpleNamespace(name=ROOT_AGENT_NAME)

        async def run_async(self, user_id, session_id, new_message):
            yield FakeEvent("ok")

    runner = FakeRunner()
    service = _service(runner)

    await service.send_async(ChatMessage(user_id="u1", text="hi"))
    await service.send_async(ChatMessage(user_id="u1", text="hi again"))

    # session_id defaults to user_id; created once, reused on the second call.
    assert runner.session_service.create_calls == [("u1", "u1")]


async def test_reset_session_deletes_existing_session():
    class FakeRunner:
        def __init__(self) -> None:
            self.session_service = FakeSessionService()
            self.agent = SimpleNamespace(name=ROOT_AGENT_NAME)

        async def run_async(self, user_id, session_id, new_message):
            yield FakeEvent("ok")

    runner = FakeRunner()
    service = _service(runner)
    await service.send_async(ChatMessage(user_id="u1", text="hi"))  # creates the session

    await service.reset_session("u1")

    assert runner.session_service.delete_calls == [("u1", "u1")]


async def test_reset_session_noop_when_no_session_exists():
    class FakeRunner:
        def __init__(self) -> None:
            self.session_service = FakeSessionService()
            self.agent = SimpleNamespace(name=ROOT_AGENT_NAME)

    runner = FakeRunner()
    service = _service(runner)

    await service.reset_session("never-seen-user")

    assert runner.session_service.delete_calls == []


async def test_send_async_serializes_calls_for_the_same_user():
    """Two messages for the same user must never run run_async concurrently
    (docs/architecture.md §6.3) — without the per-user lock this interleaves
    session creation/run_async and can corrupt the shared ADK session."""
    log: list[str] = []
    started = asyncio.Event()
    release = asyncio.Event()

    class FakeRunner:
        def __init__(self) -> None:
            self.session_service = FakeSessionService()
            self.agent = SimpleNamespace(name=ROOT_AGENT_NAME)

        async def run_async(self, user_id, session_id, new_message):
            log.append(f"start:{user_id}")
            started.set()
            await release.wait()
            log.append(f"end:{user_id}")
            yield FakeEvent(f"reply-{user_id}")

    service = _service(FakeRunner())

    task1 = asyncio.create_task(
        service.send_async(ChatMessage(user_id="u1", text="first"))
    )
    await started.wait()
    started.clear()

    task2 = asyncio.create_task(
        service.send_async(ChatMessage(user_id="u1", text="second"))
    )
    # Give task2 every opportunity to run — it must block on the lock and
    # never even reach run_async while task1 still holds it.
    for _ in range(5):
        await asyncio.sleep(0)
    assert not started.is_set()
    assert log == ["start:u1"]

    release.set()
    result1 = await task1
    result2 = await task2

    assert log == ["start:u1", "end:u1", "start:u1", "end:u1"]
    assert result1 == "reply-u1"
    assert result2 == "reply-u1"


async def test_send_async_does_not_serialize_different_users():
    """The lock is per-user_id: a stuck call for one user must not block a
    concurrent call for another user."""
    log: list[str] = []
    release_u1 = asyncio.Event()

    class FakeRunner:
        def __init__(self) -> None:
            self.session_service = FakeSessionService()
            self.agent = SimpleNamespace(name=ROOT_AGENT_NAME)

        async def run_async(self, user_id, session_id, new_message):
            log.append(f"start:{user_id}")
            if user_id == "u1":
                await release_u1.wait()
            log.append(f"end:{user_id}")
            yield FakeEvent(f"reply-{user_id}")

    service = _service(FakeRunner())

    task1 = asyncio.create_task(
        service.send_async(ChatMessage(user_id="u1", text="hi"))
    )
    await asyncio.sleep(0)  # let task1 reach the block on release_u1

    result2 = await service.send_async(ChatMessage(user_id="u2", text="hello"))

    assert result2 == "reply-u2"
    assert log == ["start:u1", "start:u2", "end:u2"]

    release_u1.set()
    result1 = await task1
    assert result1 == "reply-u1"
