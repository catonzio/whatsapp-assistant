from whatsapp_assistant.agents.tools.lists_tools import ListsRepository
from whatsapp_assistant.database.models.list import List, ListItem

from db_utils import make_sqlite_sessionmaker


async def _repo() -> ListsRepository:
    sessionmaker = await make_sqlite_sessionmaker(List.__table__, ListItem.__table__)
    return ListsRepository(sessionmaker=sessionmaker)


async def test_create_list_and_find_lists():
    repo = await _repo()

    created = await repo.create_list(list_type="shopping", name="Spesa settimanale")
    assert created["success"] is True

    result = await repo.find_lists(list_type="shopping")
    assert [row["name"] for row in result["lists"]] == ["Spesa settimanale"]

    tasks = await repo.find_lists(list_type="task")
    assert tasks["lists"] == []


async def test_add_list_item_and_list_items_excludes_checked_by_default():
    repo = await _repo()
    created = await repo.create_list(list_type="shopping", name="Spesa")
    list_id = created["list_id"]
    item = await repo.add_list_item(list_id, "Pane")
    await repo.add_list_item(list_id, "Latte")
    await repo.check_list_item(item["list_item_id"])

    result = await repo.list_items(list_id)

    assert [i["description"] for i in result["items"]] == ["Latte"]


async def test_list_items_include_checked():
    repo = await _repo()
    created = await repo.create_list(list_type="shopping", name="Spesa")
    list_id = created["list_id"]
    item = await repo.add_list_item(list_id, "Pane")
    await repo.check_list_item(item["list_item_id"])

    result = await repo.list_items(list_id, include_checked=True)

    assert len(result["items"]) == 1
    assert result["items"][0]["is_checked"] is True


async def test_check_list_item_can_be_unchecked():
    repo = await _repo()
    created = await repo.create_list(list_type="shopping", name="Spesa")
    item = await repo.add_list_item(created["list_id"], "Pane")

    await repo.check_list_item(item["list_item_id"], checked=True)
    await repo.check_list_item(item["list_item_id"], checked=False)

    result = await repo.list_items(created["list_id"])
    assert [i["description"] for i in result["items"]] == ["Pane"]


async def test_check_list_item_not_found():
    repo = await _repo()

    result = await repo.check_list_item(list_item_id=999)

    assert result == {"success": False, "error": "not_found"}


async def test_remove_list_item():
    repo = await _repo()
    created = await repo.create_list(list_type="task", name="Task condivisi")
    item = await repo.add_list_item(
        created["list_id"], "Prenotare ristorante", attributes={"priority": "alta"}
    )

    result = await repo.remove_list_item(item["list_item_id"])

    assert result == {"success": True}
    listed = await repo.list_items(created["list_id"], include_checked=True)
    assert listed["items"] == []


async def test_remove_list_item_not_found():
    repo = await _repo()

    result = await repo.remove_list_item(list_item_id=999)

    assert result == {"success": False, "error": "not_found"}
