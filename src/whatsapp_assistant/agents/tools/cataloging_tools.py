"""Cataloging + retrieval tools for CatalogingAgent (docs/architecture.md
§8.3, requirements.md §4.2/§4.3).

Each public method is registered as an ADK tool (as a bound method) by
`cataloging_agent.py` — its docstring/type hints double as the tool's schema
for the LLM, same convention `google.adk`'s automatic function calling uses
for any plain callable.
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from whatsapp_assistant.agents.tools.place_lookup import PlaceLookup
from whatsapp_assistant.agents.wrappers import may_fail_async
from whatsapp_assistant.database.models.category import Category
from whatsapp_assistant.database.models.item import Item

logger = logging.getLogger("whatsapp-assistant")


class CatalogingRepository:
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        place_lookup: PlaceLookup,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._place_lookup = place_lookup

    @may_fail_async
    async def search_categories(self, query: str | None = None) -> dict:
        """List existing categories, optionally filtered by name.

        Call this before deciding whether to invent a new category: if a
        similar one already exists (e.g. "viaggi"), reuse it instead of
        creating a near-duplicate.

        Args:
            query: optional case-insensitive substring to filter category names.

        Returns:
            {"success": True, "categories": [{"id", "name", "description"}, ...]}
        """
        async with self._sessionmaker() as session:
            stmt = select(Category)
            if query:
                stmt = stmt.where(Category.name.ilike(f"%{query}%"))
            result = await session.execute(stmt.order_by(Category.name))
            categories = result.scalars().all()

        return {
            "success": True,
            "categories": [
                {"id": c.id, "name": c.name, "description": c.description}
                for c in categories
            ],
        }

    @may_fail_async
    async def verify_place(
        self, name: str, location_hint: str | None = None
    ) -> dict:
        """Check via an external place-lookup service whether `name` is a
        real place and, if so, what kind (e.g. a restaurant).

        Call this before auto-creating a "ristoranti" category from a bare
        place name — do not trust the user's wording alone.

        Args:
            name: the place name as written by the user.
            location_hint: optional city/area to disambiguate the search.

        Returns:
            {"success": True, "found": bool, "is_restaurant": bool | None,
             "name": str | None, "address": str | None, "rating": float | None}
        """
        info = await self._place_lookup.lookup(name, location_hint, limit=1)
        info = info[0] if info else None
        if not info:
            return {
                "success": True,
                "found": False,
                "is_restaurant": None,
                "name": None,
                "address": None,
                "rating": None,
            }
        return {
            "success": True,
            "found": info.found,
            "is_restaurant": info.is_restaurant,
            "name": info.name,
            "address": info.address,
            "rating": info.rating,
        }

    @may_fail_async
    async def find_similar_items(
        self, name: str, category: str | None = None
    ) -> dict:
        """Find already-saved items with a similar name, to avoid creating a
        duplicate row when the user re-mentions something already catalogued.

        Args:
            name: the candidate item name to check for duplicates.
            category: optional category name to narrow the search.

        Returns:
            {"success": True, "matches": [{"id", "name", "category", "rating"}, ...]}
        """
        async with self._sessionmaker() as session:
            category_id = None
            if category:
                category_id = await session.scalar(
                    select(Category.id).where(Category.name == category)
                )

            dialect = session.bind.dialect.name if session.bind else ""
            if dialect == "postgresql":
                # pg_trgm similarity — see alembic migration
                # 234761436f4d_enable_pg_trgm_and_index_items_name.
                similarity = func.similarity(Item.name, name)
                stmt = select(Item).where(similarity > 0.3)
                if category_id is not None:
                    stmt = stmt.where(Item.category_id == category_id)
                stmt = stmt.order_by(similarity.desc()).limit(5)
            else:
                # SQLite (unit tests) has no pg_trgm — plain substring match
                # is enough for test coverage, never used against real Postgres.
                stmt = select(Item).where(Item.name.ilike(f"%{name}%"))
                if category_id is not None:
                    stmt = stmt.where(Item.category_id == category_id)
                stmt = stmt.limit(5)

            items = list((await session.execute(stmt)).scalars().all())

            matches = []
            for item in items:
                cat_name = await session.scalar(
                    select(Category.name).where(Category.id == item.category_id)
                )
                matches.append(
                    {
                        "id": item.id,
                        "name": item.name,
                        "category": cat_name,
                        "rating": (
                            float(item.rating) if item.rating is not None else None
                        ),
                    }
                )

        return {"success": True, "matches": matches}

    @may_fail_async
    async def save_item(
        self,
        category: str,
        name: str,
        notes: str | None = None,
        rating: float | None = None,
        location: str | None = None,
        attributes: dict | None = None,
    ) -> dict:
        """Save a new catalogued item, creating its category if it doesn't
        exist yet.

        Args:
            category: category name (existing or new — e.g. "ristoranti", "libri").
            name: the item's name.
            notes: free-text notes/review.
            rating: numeric rating given by the user, if any.
            location: free-text location (e.g. city), useful for retrieval.
            attributes: category-specific fields as a flat dict (e.g.
                {"cuisine": "giapponese"} for a restaurant, {"author": "..."}
                for a book).

        Returns:
            {"success": True, "item_id": int, "category": str}
        """
        async with self._sessionmaker() as session:
            category_row = await session.scalar(
                select(Category).where(Category.name == category)
            )
            if category_row is None:
                category_row = Category(name=category)
                session.add(category_row)
                await session.flush()

            item = Item(
                category_id=category_row.id,
                name=name,
                notes=notes,
                rating=rating,
                location=location,
                attributes=attributes,
            )
            session.add(item)
            await session.commit()
            return {
                "success": True,
                "item_id": item.id,
                "category": category_row.name,
            }

    @may_fail_async
    async def update_item(
        self,
        item_id: int,
        notes: str | None = None,
        rating: float | None = None,
        location: str | None = None,
        attributes: dict | None = None,
    ) -> dict:
        """Update fields of an already-saved item (found via
        `find_similar_items` or `search_items`). Only the provided fields
        are changed.

        Args:
            item_id: id of the item to update.
            notes: new notes/review text, if changing.
            rating: new rating, if changing.
            location: new location, if changing.
            attributes: new attributes dict, if changing (replaces the whole
                dict, not a per-key merge).

        Returns:
            {"success": True, "item_id": int} or
            {"success": False, "error": "not_found"}
        """
        async with self._sessionmaker() as session:
            item = await session.get(Item, item_id)
            if item is None:
                return {"success": False, "error": "not_found"}
            if notes is not None:
                item.notes = notes
            if rating is not None:
                item.rating = rating
            if location is not None:
                item.location = location
            if attributes is not None:
                item.attributes = attributes
            await session.commit()
            return {"success": True, "item_id": item.id}

    @may_fail_async
    async def search_items(
        self,
        category: str | None = None,
        name: str | None = None,
        location: str | None = None,
        free_text: str | None = None,
    ) -> dict:
        """Retrieve catalogued items matching the given filters, to answer
        questions like "che ristoranti abbiamo salvato a Roma?".

        Args:
            category: exact category name to filter by.
            name: substring to match against the item name.
            location: substring to match against the item location.
            free_text: substring matched against name, notes and location
                combined — use this for loosely-phrased questions instead of
                guessing a single field.

        Returns:
            {"success": True, "items": [{"id", "name", "category", "notes",
             "rating", "location", "attributes"}, ...]}
        """
        async with self._sessionmaker() as session:
            stmt = select(Item, Category.name).join(
                Category, Item.category_id == Category.id
            )
            if category:
                stmt = stmt.where(Category.name == category)
            if name:
                stmt = stmt.where(Item.name.ilike(f"%{name}%"))
            if location:
                stmt = stmt.where(Item.location.ilike(f"%{location}%"))
            if free_text:
                like = f"%{free_text}%"
                stmt = stmt.where(
                    Item.name.ilike(like)
                    | Item.notes.ilike(like)
                    | Item.location.ilike(like)
                )
            rows = (await session.execute(stmt.limit(20))).all()

        return {
            "success": True,
            "items": [
                {
                    "id": item.id,
                    "name": item.name,
                    "category": cat_name,
                    "notes": item.notes,
                    "rating": (
                        float(item.rating) if item.rating is not None else None
                    ),
                    "location": item.location,
                    "attributes": item.attributes,
                }
                for item, cat_name in rows
            ],
        }
