from whatsapp_assistant.configs.settings import get_settings

from .orchestrator_agent import build_root_agent


settings = get_settings()
root_agent = build_root_agent(
    orchestrator_model=settings.gemini_model_orchestrator,
    subagents_model=settings.gemini_model_subagent,
)

__all__ = ["build_root_agent", "root_agent"]
