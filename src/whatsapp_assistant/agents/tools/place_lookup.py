"""Place verification for the cataloging agent (docs/architecture.md §8.3,
requirements.md §4.2 — "verificare tramite un tool che si tratti
effettivamente di un ristorante").

Hidden behind a `Protocol` (same pattern already used for `ObjectStorage`,
see docs/architecture.md §5) so the provider can move from Google Places
(paid per call) to OSM Nominatim (free, rate-limited) without touching any
agent/tool code — only `get_place_lookup()` needs to change what it builds.

Google's own `google_maps_grounding` built-in ADK tool is NOT usable here:
it requires the Vertex AI variant of the Gemini API
(`GOOGLE_GENAI_USE_ENTERPRISE=TRUE`), while this project talks to the
Gemini API directly with a plain API key (see gemini_media.py). Hence a
plain HTTP-based tool instead of a built-in one.
"""

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx

from whatsapp_assistant.configs.settings import Settings

logger = logging.getLogger("whatsapp-assistant")


@dataclass
class PlaceInfo:
    found: bool
    name: str | None = None
    is_restaurant: bool | None = None
    address: str | None = None
    rating: float | None = None


class PlaceLookup(Protocol):
    async def lookup(
        self, name: str, location_hint: str | None = None, limit: int = 5
    ) -> list[PlaceInfo]: ...


_GOOGLE_RESTAURANT_TYPES = {
    "restaurant",
    "meal_takeaway",
    "meal_delivery",
    "cafe",
    "bar",
}

_OSM_RESTAURANT_TYPES = {"restaurant", "fast_food", "cafe", "bar", "pub"}


class GoogleMapsPlaceLookup:
    """Default provider: Google Places API (Text Search v1), paid per request."""

    _SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def lookup(
        self, name: str, location_hint: str | None = None, limit: int = 5
    ) -> list[PlaceInfo]:
        query = f"{name} {location_hint}" if location_hint else name
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.post(
                self._SEARCH_URL,
                headers={
                    "X-Goog-Api-Key": self._api_key,
                    "X-Goog-FieldMask": (
                        "places.displayName,places.types,"
                        "places.formattedAddress,places.rating"
                    ),
                },
                json={"textQuery": query, "pageSize": max(1, min(limit, 20))},
            )
            resp.raise_for_status()
            data = resp.json()

        places = data.get("places") or []
        if not places:
            return []

        place_infos = []
        for place in places:
            types = set(place.get("types") or [])
            place_infos.append(
                PlaceInfo(
                    found=True,
                    name=(place.get("displayName") or {}).get("text"),
                    is_restaurant=bool(types & _GOOGLE_RESTAURANT_TYPES),
                    address=place.get("formattedAddress"),
                    rating=place.get("rating"),
                )
            )
        return place_infos


class NominatimPlaceLookup:
    """Free fallback provider: OpenStreetMap Nominatim.

    Rate-limited (Nominatim's usage policy asks for max 1 request/second) and
    coarser category data than Google Places, but free — switch to this via
    `PLACE_LOOKUP_PROVIDER=osm` if Google Places costs eat into the monthly
    budget (requirements.md §6).
    """

    _SEARCH_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, user_agent: str = "whatsapp-assistant/0.1") -> None:
        self._user_agent = user_agent

    async def lookup(
        self, name: str, location_hint: str | None = None, limit: int = 5
    ) -> list[PlaceInfo]:
        query = f"{name} {location_hint}" if location_hint else name
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(
                self._SEARCH_URL,
                headers={"User-Agent": self._user_agent},
                params={"q": query, "format": "jsonv2", "limit": limit},
            )
            resp.raise_for_status()
            results = resp.json()

        if not results:
            return []

        def is_restaurant(result: dict) -> bool:
            return (
                result.get("category") == "amenity"
                and result.get("type") in _OSM_RESTAURANT_TYPES
            )

        return [
            PlaceInfo(
                found=True,
                name=result.get("display_name"),
                is_restaurant=is_restaurant(result),
                address=result.get("display_name"),
                rating=None,  # Nominatim doesn't provide ratings.
            )
            for result in results
        ]


def get_place_lookup(settings: Settings) -> PlaceLookup:
    if settings.place_lookup_provider == "osm":
        return NominatimPlaceLookup()
    if settings.place_lookup_provider != "google":
        raise ValueError(
            f"Unknown PLACE_LOOKUP_PROVIDER: {settings.place_lookup_provider!r}"
        )
    if not settings.google_maps_api_key:
        raise ValueError(
            "PLACE_LOOKUP_PROVIDER=google requires GOOGLE_MAPS_API_KEY to be set"
        )
    return GoogleMapsPlaceLookup(api_key=settings.google_maps_api_key)


if __name__ == "__main__":
    import asyncio
    from whatsapp_assistant.configs.settings import get_settings

    async def main():
        settings = get_settings()
        lookup = get_place_lookup(settings)
        info = await lookup.lookup("Da Mario", location_hint="Roma")
        print(info)

    asyncio.run(main())
