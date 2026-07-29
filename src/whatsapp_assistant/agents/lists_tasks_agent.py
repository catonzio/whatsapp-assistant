"""ListsTasksAgent (docs/architecture.md §8.5): shared shopping lists and
tasks. requirements.md §4.4.
"""

from google.adk import Agent

from whatsapp_assistant.agents.tools.lists_tools import ListsRepository
from whatsapp_assistant.database.session import get_sessionmaker

_INSTRUCTION = """
Gestisci liste della spesa e task condivisi. Rispondi in italiano.

Prima di creare una nuova lista, usa find_lists per controllare se ne esiste
già una adatta (es. una lista della spesa attiva) invece di crearne una
nuova ogni volta.

Per i task, priorità/scadenza/assegnatario vanno nel campo attributes di
add_list_item (es. {"priority": "alta", "due_date": "...", "assigned_to":
"..."}), non in campi separati.

Quando elenchi una lista, per default mostra solo le voci non ancora
completate (include_checked=False), a meno che l'utente chieda
esplicitamente anche quelle già fatte/comprate.
""".strip()


def build_lists_tasks_agent(subagent_model: str) -> Agent:
    repository = ListsRepository(sessionmaker=get_sessionmaker())
    return Agent(
        name="ListsTasksAgent",
        model=subagent_model,
        description="Gestisce liste della spesa e task condivisi tra i due utenti.",
        instruction=_INSTRUCTION,
        mode="single_turn",
        tools=[
            repository.create_list,
            repository.find_lists,
            repository.add_list_item,
            repository.check_list_item,
            repository.remove_list_item,
            repository.list_items,
        ],
    )
