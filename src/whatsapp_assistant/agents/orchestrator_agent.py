"""Root orchestrator agent (docs/architecture.md §8).

Single entry point for the ADK `Runner`. Owns intent routing across the
three domain sub-agents, Italian conversational tone, and session-level
behaviors — no direct DB tools of its own, so its own instructions stay
short (it runs on every message; the domain sub-agents run on a cheaper
model, see Settings.gemini_model_subagent).

Multimodal note (§8.2): domain sub-agents run inline in this agent's own
ADK session (`mode="single_turn"`), which propagates multimodal content
better than the legacy `AgentTool` wrapper. As a robustness measure that
doesn't depend on that session/branch propagation being exact, the
instruction below still asks the orchestrator to describe any image
explicitly in the delegation request.

Built lazily via `build_root_agent()` rather than as a module-level
constant: constructing a domain agent touches `get_place_lookup()`, which
can raise if Google Places is selected without an API key configured — that
must fail when a `Runner` is actually built (see
services/chat_service/impls/adk_chat_service.py), not at import time (which
would break plain `import whatsapp_assistant` in contexts — e.g. tests —
that never construct a real Runner).
"""

from google.adk import Agent

from whatsapp_assistant.agents.cataloging_agent import build_cataloging_agent
from whatsapp_assistant.agents.lists_tasks_agent import build_lists_tasks_agent
from whatsapp_assistant.agents.reminders_agent import build_reminders_agent

_INSTRUCTION = """
Sei l'assistente WhatsApp personale di una coppia. Rispondi sempre in
italiano, in modo breve e naturale, come in una chat.

Hai a disposizione tre agenti specializzati, richiamabili come strumenti:
- CatalogingAgent: per salvare o recuperare ristoranti, libri, film, viaggi,
  canzoni e qualunque altra informazione da catalogare, incluse domande di
  recupero ("che ristoranti abbiamo salvato a Roma?") e link da salvare.
- RemindersAgent: per creare, modificare, elencare o cancellare promemoria
  ed eventi.
- ListsTasksAgent: per liste della spesa e task condivisi.

Quando deleghi, scrivi nel campo "request" una descrizione completa e
autosufficiente di cosa serve fare — includi tutti i dettagli rilevanti
(nome, categoria, date, numeri) che hai capito dal messaggio dell'utente.

Se il messaggio contiene una foto, descrivi sempre nel campo "request" cosa
mostra l'immagine (es. nome del locale su un'insegna, piatti su un menu),
così l'agente delegato può agire di conseguenza anche se non vedesse
l'immagine direttamente.

Componi tu la risposta finale per l'utente a partire da quello che
l'agente delegato restituisce — non limitarti a incollarla, adattala al
tono della conversazione.
""".strip()


def build_root_agent(orchestrator_model: str, subagents_model: str) -> Agent:
    return Agent(
        name="OrchestratorAssistant",
        model=orchestrator_model,
        description=(
            "Assistente WhatsApp personale — smista le richieste agli agenti "
            "di dominio (catalogazione, promemoria, liste/task)."
        ),
        instruction=_INSTRUCTION,
        sub_agents=[
            build_cataloging_agent(subagents_model),
            build_reminders_agent(subagents_model),
            build_lists_tasks_agent(subagents_model),
        ],
    )
