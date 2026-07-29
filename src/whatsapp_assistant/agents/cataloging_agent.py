"""CatalogingAgent (docs/architecture.md §8.3): items + categories, both
writing and retrieval. requirements.md §4.2/§4.3.

`mode="single_turn"`: registered by the orchestrator as an inline tool
(`sub_agents=[...]`), not with the legacy `AgentTool` wrapper — current ADK
guidance discourages `AgentTool` directly in favor of this mode, and it also
runs the sub-agent as a node inside the parent's own session rather than a
throwaway one, which is materially better for forwarding multimodal content
(see google/adk-python#729, and the caveat in docs/architecture.md §8.2).
"""

from google.adk import Agent

from whatsapp_assistant.agents.tools.cataloging_tools import CatalogingRepository
from whatsapp_assistant.agents.tools.link_metadata import fetch_link_metadata
from whatsapp_assistant.agents.tools.place_lookup import get_place_lookup
from whatsapp_assistant.configs.settings import get_settings
from whatsapp_assistant.database.session import get_sessionmaker

_INSTRUCTION_TEMPLATE = """
Gestisci la catalogazione di informazioni (ristoranti, libri, film, viaggi,
canzoni, ecc.) e il loro recupero. Rispondi in italiano.

Prima di salvare un nuovo elemento:
1. Usa search_categories per vedere se esiste già una categoria adatta;
   inferisci la categoria dal contesto (es. se esiste già "viaggi" e
   l'utente scrive il nome di una città, è probabilmente un viaggio) prima
   di inventarne una nuova.
2. Se il nome sembra un locale/ristorante, usa verify_place per confermarlo
   prima di creare/usare la categoria "ristoranti" — non fidarti solo del
   nome scritto dall'utente.
3. Usa find_similar_items per controllare se l'elemento esiste già: se sì,
   proponi un update_item invece di crearne uno duplicato.
4. Se il messaggio contiene un link, {link_behavior}

Per rispondere a domande di recupero ("che ristoranti abbiamo salvato a
Roma?") usa search_items con i filtri più adatti alla domanda.
""".strip()


def build_cataloging_agent(subagent_model: str) -> Agent:
    settings = get_settings()
    repository = CatalogingRepository(
        sessionmaker=get_sessionmaker(),
        place_lookup=get_place_lookup(settings),
    )
    link_behavior = (
        "usa subito fetch_link_metadata per arricchirlo con titolo/descrizione."
        if settings.link_auto_fetch
        else (
            "chiedi prima conferma all'utente se vuole che tu apra il link per "
            "estrarre titolo/descrizione, e chiama fetch_link_metadata solo "
            "dopo una risposta affermativa."
        )
    )
    return Agent(
        name="CatalogingAgent",
        model=subagent_model,
        description=(
            "Salva e recupera informazioni catalogate (ristoranti, libri, "
            "film, viaggi, canzoni, ecc.), incluse categorie inferite e link."
        ),
        instruction=_INSTRUCTION_TEMPLATE.format(link_behavior=link_behavior),
        mode="single_turn",
        tools=[
            repository.search_categories,
            repository.verify_place,
            repository.find_similar_items,
            repository.save_item,
            repository.update_item,
            repository.search_items,
            fetch_link_metadata,
        ],
    )
