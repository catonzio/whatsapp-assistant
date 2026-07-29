"""Structural tests for the agent tree (docs/architecture.md §8): the
orchestrator must expose exactly the 3 domain sub-agents as single-turn
tools, and each sub-agent must expose its expected tool set. These don't
call a real Gemini model — they only check the ADK object graph is wired as
designed.
"""

from google.adk import Agent
import pytest

from whatsapp_assistant.configs.settings import get_settings
from whatsapp_assistant.database.session import get_engine, get_sessionmaker

settings = get_settings()


@pytest.fixture(autouse=True)
def _settings_cache_isolation(monkeypatch):
    """Force PLACE_LOOKUP_PROVIDER=osm so building the cataloging agent never
    needs a real GOOGLE_MAPS_API_KEY, then restore the process-wide settings
    singletons so other test modules see secrets/.env again."""
    monkeypatch.setenv("PLACE_LOOKUP_PROVIDER", "osm")
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()


def test_root_agent_exposes_three_single_turn_domain_tools():
    from whatsapp_assistant.agents.orchestrator_agent import build_root_agent

    root = build_root_agent(
        orchestrator_model=settings.gemini_model_orchestrator,
        subagents_model=settings.gemini_model_subagent,
    )

    assert root.name == "OrchestratorAssistant"
    assert [a.name for a in root.sub_agents] == [
        "CatalogingAgent",
        "RemindersAgent",
        "ListsTasksAgent",
    ]
    assert all(
        a.mode == "single_turn" if isinstance(a, Agent) else False
        for a in root.sub_agents
    )
    # No direct DB tools on the orchestrator itself (routing/composition only).
    assert root.tools == [] or all(
        t.__class__.__name__ == "_SingleTurnAgentTool" for t in root.tools
    )


def test_cataloging_agent_exposes_expected_tools():
    from whatsapp_assistant.agents.cataloging_agent import build_cataloging_agent

    agent = build_cataloging_agent(subagent_model=settings.gemini_model_subagent)

    tool_names = {t.__name__ for t in agent.tools}
    assert tool_names == {
        "search_categories",
        "verify_place",
        "find_similar_items",
        "save_item",
        "update_item",
        "search_items",
        "fetch_link_metadata",
    }


def test_cataloging_agent_instructs_confirmation_by_default(monkeypatch):
    from whatsapp_assistant.agents.cataloging_agent import build_cataloging_agent

    monkeypatch.delenv("LINK_AUTO_FETCH", raising=False)
    get_settings.cache_clear()

    agent = build_cataloging_agent(subagent_model=settings.gemini_model_subagent)

    assert "chiedi prima conferma" in str(agent.instruction)


def test_cataloging_agent_instructs_auto_fetch_when_enabled(monkeypatch):
    from whatsapp_assistant.agents.cataloging_agent import build_cataloging_agent

    monkeypatch.setenv("LINK_AUTO_FETCH", "true")
    get_settings.cache_clear()

    agent = build_cataloging_agent(subagent_model=settings.gemini_model_subagent)

    assert "usa subito fetch_link_metadata" in str(agent.instruction)


def test_reminders_agent_exposes_expected_tools():
    from whatsapp_assistant.agents.reminders_agent import build_reminders_agent

    agent = build_reminders_agent(subagent_model=settings.gemini_model_subagent)

    tool_names = {t.__name__ for t in agent.tools}
    assert tool_names == {
        "create_reminder",
        "list_reminders",
        "update_reminder",
        "cancel_reminder",
    }


def test_lists_tasks_agent_exposes_expected_tools():
    from whatsapp_assistant.agents.lists_tasks_agent import build_lists_tasks_agent

    agent = build_lists_tasks_agent(subagent_model=settings.gemini_model_subagent)

    tool_names = {t.__name__ for t in agent.tools}
    assert tool_names == {
        "create_list",
        "find_lists",
        "add_list_item",
        "check_list_item",
        "remove_list_item",
        "list_items",
    }


def test_root_agent_construction_fails_fast_without_google_maps_key(monkeypatch):
    """place_lookup_provider defaults to "google" (your explicit choice) —
    building the agent tree must fail loudly if no key is configured, not
    silently fall back, mirroring the existing database_url pattern."""
    from whatsapp_assistant.agents.orchestrator_agent import build_root_agent

    monkeypatch.setenv("PLACE_LOOKUP_PROVIDER", "google")
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="GOOGLE_MAPS_API_KEY"):
        build_root_agent(
            orchestrator_model=settings.gemini_model_orchestrator,
            subagents_model=settings.gemini_model_subagent,
        )
