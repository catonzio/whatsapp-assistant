"""Minimal placeholder root agent.

TEMPORARY: exists only to make the ChatService/Runner plumbing testable
end-to-end before the real domain agents (cataloging, reminders, shared
lists) are designed — see docs/architecture.md §7, point 2 ("Design degli
agenti ADK per il dominio"). No tools, no sub-agents. Replace this whole
module once that design is done.
"""

from google.adk import Agent

GEMINI_MODEL = "gemini-2.5-flash"

root_agent = Agent(
    name="PlaceholderAssistant",
    model=GEMINI_MODEL,
    description="Placeholder assistant, used only to test the chat plumbing.",
    instruction=(
        "You are a placeholder assistant for a personal WhatsApp assistant "
        "app still under development. Reply briefly and mention that your "
        "real capabilities (cataloging, reminders, shared lists) are not "
        "implemented yet."
    ),
)
