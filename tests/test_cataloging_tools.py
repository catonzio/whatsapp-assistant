from whatsapp_assistant.agents.tools.cataloging_tools import CatalogingRepository
from whatsapp_assistant.agents.tools.place_lookup import PlaceInfo
from whatsapp_assistant.database.models.category import Category
from whatsapp_assistant.database.models.item import Item

from db_utils import make_sqlite_sessionmaker


class FakePlaceLookup:
    def __init__(self, info: PlaceInfo) -> None:
        self._info = info
        self.calls: list[tuple[str, str | None]] = []

    async def lookup(
        self, name: str, location_hint: str | None = None, limit: int = 5
    ) -> list[PlaceInfo]:
        self.calls.append((name, location_hint))
        return [self._info]


async def _repo(place_lookup=None) -> CatalogingRepository:
    sessionmaker = await make_sqlite_sessionmaker(Category.__table__, Item.__table__)
    return CatalogingRepository(
        sessionmaker=sessionmaker,
        place_lookup=place_lookup or FakePlaceLookup(PlaceInfo(found=False)),
    )


async def test_save_item_creates_category_when_missing():
    repo = await _repo()

    result = await repo.save_item(category="ristoranti", name="Da Mario", rating=4.5)

    assert result["success"] is True
    assert result["category"] == "ristoranti"

    categories = await repo.search_categories()
    assert [c["name"] for c in categories["categories"]] == ["ristoranti"]


async def test_save_item_reuses_existing_category():
    repo = await _repo()
    await repo.save_item(category="ristoranti", name="Da Mario")

    await repo.save_item(category="ristoranti", name="Osteria Bella")

    categories = await repo.search_categories()
    assert len(categories["categories"]) == 1


async def test_search_categories_filters_by_query():
    repo = await _repo()
    await repo.save_item(category="ristoranti", name="Da Mario")
    await repo.save_item(category="viaggi", name="Roma")

    result = await repo.search_categories(query="risto")

    assert [c["name"] for c in result["categories"]] == ["ristoranti"]


async def test_verify_place_delegates_to_place_lookup():
    place_lookup = FakePlaceLookup(
        PlaceInfo(found=True, name="Da Mario", is_restaurant=True, rating=4.2)
    )
    repo = await _repo(place_lookup)

    result = await repo.verify_place("Da Mario", "Roma")

    assert result["success"] is True
    assert result["is_restaurant"] is True
    assert place_lookup.calls == [("Da Mario", "Roma")]


async def test_update_item_changes_only_provided_fields():
    repo = await _repo()
    saved = await repo.save_item(
        category="ristoranti", name="Da Mario", notes="buono", rating=3.0
    )
    item_id = saved["item_id"]

    result = await repo.update_item(item_id, rating=4.5)

    assert result["success"] is True
    items = await repo.search_items(category="ristoranti")
    item = items["items"][0]
    assert item["rating"] == 4.5
    assert item["notes"] == "buono"  # untouched


async def test_update_item_not_found():
    repo = await _repo()

    result = await repo.update_item(item_id=999, rating=1.0)

    assert result == {"success": False, "error": "not_found"}


async def test_update_item_changes_location_and_attributes():
    repo = await _repo()
    saved = await repo.save_item(category="ristoranti", name="Da Mario")

    result = await repo.update_item(
        saved["item_id"],
        notes="rivisto, ottimo",
        location="Milano",
        attributes={"cuisine": "giapponese"},
    )

    assert result["success"] is True
    items = await repo.search_items(category="ristoranti")
    item = items["items"][0]
    assert item["notes"] == "rivisto, ottimo"
    assert item["location"] == "Milano"
    assert item["attributes"] == {"cuisine": "giapponese"}


async def test_find_similar_items_matches_by_substring_on_sqlite():
    repo = await _repo()
    await repo.save_item(category="ristoranti", name="Trattoria da Mario")

    result = await repo.find_similar_items(name="Mario")

    assert result["success"] is True
    assert result["matches"][0]["name"] == "Trattoria da Mario"


async def test_find_similar_items_filters_by_category():
    repo = await _repo()
    await repo.save_item(category="ristoranti", name="Mario's")
    await repo.save_item(category="libri", name="Mario's Diary")

    result = await repo.find_similar_items(name="Mario", category="ristoranti")

    assert [m["name"] for m in result["matches"]] == ["Mario's"]


async def test_find_similar_items_no_match():
    repo = await _repo()
    await repo.save_item(category="ristoranti", name="Trattoria da Mario")

    result = await repo.find_similar_items(name="Sushi Bar")

    assert result["matches"] == []


async def test_search_items_free_text_matches_notes():
    repo = await _repo()
    await repo.save_item(
        category="ristoranti",
        name="Da Mario",
        notes="ottima pizza romana",
        location="Roma",
    )
    await repo.save_item(category="ristoranti", name="Sushi Bar", location="Milano")

    result = await repo.search_items(free_text="romana")

    assert len(result["items"]) == 1
    assert result["items"][0]["name"] == "Da Mario"


async def test_search_items_filters_by_name():
    repo = await _repo()
    await repo.save_item(category="ristoranti", name="Da Mario")
    await repo.save_item(category="ristoranti", name="Sushi Bar")

    result = await repo.search_items(name="Mario")

    assert [i["name"] for i in result["items"]] == ["Da Mario"]


async def test_search_items_filters_by_location():
    repo = await _repo()
    await repo.save_item(category="ristoranti", name="Da Mario", location="Roma")
    await repo.save_item(category="ristoranti", name="Sushi Bar", location="Milano")

    result = await repo.search_items(location="Roma")

    assert [i["name"] for i in result["items"]] == ["Da Mario"]
