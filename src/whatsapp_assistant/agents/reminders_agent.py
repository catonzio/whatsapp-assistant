"""RemindersAgent (docs/architecture.md §8.4): CRUD for reminders/events.
requirements.md §4.1.

Deliberately excludes proactive sending and budget-gating — see the module
docstring in agents/tools/reminders_tools.py and docs/architecture.md §10
point 1.
"""

from google.adk import Agent

from whatsapp_assistant.agents.tools.reminders_tools import RemindersRepository
from whatsapp_assistant.database.session import get_sessionmaker

_INSTRUCTION = """
Gestisci promemoria ed eventi (creazione, modifica, elenco, cancellazione).
Rispondi in italiano.

Quando l'utente esprime una data/ora relativa ("domani alle 9", "il 3
agosto"), convertila in un datetime ISO-8601 assoluto prima di chiamare
create_reminder o update_reminder — non passare mai testo libero come
due_at. Se l'utente non specifica un fuso orario, assumi Europe/Rome.

Per eventi ricorrenti (compleanni, anniversari, appuntamenti settimanali),
esprimi la ricorrenza come stringa RRULE (RFC 5545), es.
"FREQ=YEARLY;INTERVAL=1" per un anniversario annuale.

Non gestisci l'invio proattivo dei promemoria: puoi solo crearli,
modificarli, elencarli o cancellarli su richiesta.
""".strip()


def build_reminders_agent(subagent_model: str) -> Agent:
    repository = RemindersRepository(sessionmaker=get_sessionmaker())
    return Agent(
        name="RemindersAgent",
        model=subagent_model,
        description="Crea, modifica, elenca e cancella promemoria ed eventi.",
        instruction=_INSTRUCTION,
        mode="single_turn",
        tools=[
            repository.create_reminder,
            repository.list_reminders,
            repository.update_reminder,
            repository.cancel_reminder,
        ],
    )
