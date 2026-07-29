import httpx
import pytest
import respx

from whatsapp_assistant.agents.tools.place_lookup import (
    GoogleMapsPlaceLookup,
    NominatimPlaceLookup,
    get_place_lookup,
)
from whatsapp_assistant.configs.settings import Settings


def _settings(**overrides) -> Settings:
    base = dict(
        whatsapp_token="t",
        whatsapp_phone_number_id="p",
        whatsapp_verify_token="v",
        whatsapp_app_secret="s",
        gemini_api_key="g",
        database_host="h",
        database_port=5432,
        database_user="u",
        database_password="pw",
        database_db="d",
        database_db_agent_sessions="a",
        database_protocol="postgresql+asyncpg",
    )
    base.update(overrides)
    return Settings(**base)


@respx.mock
async def test_google_maps_lookup_identifies_restaurant():
    respx.post("https://places.googleapis.com/v1/places:searchText").mock(
        return_value=httpx.Response(
            200,
            json={
                "places": [
                    {
                        "displayName": {"text": "Trattoria da Mario"},
                        "types": ["restaurant", "point_of_interest"],
                        "formattedAddress": "Via Roma 1, Roma",
                        "rating": 4.5,
                    }
                ]
            },
        )
    )

    lookup = GoogleMapsPlaceLookup(api_key="KEY")
    info = await lookup.lookup("da Mario", "Roma", limit=1)
    info = info[0] if info else None

    assert info is not None
    assert info.found is True
    assert info.is_restaurant is True
    assert info.name == "Trattoria da Mario"
    assert info.rating == 4.5


@respx.mock
async def test_google_maps_lookup_not_found():
    respx.post("https://places.googleapis.com/v1/places:searchText").mock(
        return_value=httpx.Response(200, json={"places": []})
    )

    lookup = GoogleMapsPlaceLookup(api_key="KEY")
    info = await lookup.lookup("qualcosa di inesistente", limit=1)
    
    assert len(info) == 0


@respx.mock
async def test_nominatim_lookup_identifies_restaurant():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "display_name": "Trattoria da Mario, Via Roma 1, Roma",
                    "category": "amenity",
                    "type": "restaurant",
                }
            ],
        )
    )

    lookup = NominatimPlaceLookup()
    info = await lookup.lookup("da Mario", "Roma", limit=1)
    info = info[0] if info else None

    assert info is not None
    assert info.found is True
    assert info.is_restaurant is True
    assert info.rating is None


@respx.mock
async def test_nominatim_lookup_non_restaurant_place():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "display_name": "Duomo di Milano",
                    "category": "tourism",
                    "type": "attraction",
                }
            ],
        )
    )

    lookup = NominatimPlaceLookup()
    info = await lookup.lookup("Duomo di Milano", limit=1)
    info = info[0] if info else None

    assert info is not None
    assert info.found is True
    assert info.is_restaurant is False


@respx.mock
async def test_nominatim_lookup_not_found():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=httpx.Response(200, json=[])
    )

    lookup = NominatimPlaceLookup()
    info = await lookup.lookup("qualcosa di inesistente", limit=1)
    
    assert len(info) == 0


def test_get_place_lookup_returns_osm_when_configured():
    settings = _settings(place_lookup_provider="osm")
    lookup = get_place_lookup(settings)
    assert isinstance(lookup, NominatimPlaceLookup)


def test_get_place_lookup_returns_google_when_configured():
    settings = _settings(place_lookup_provider="google", google_maps_api_key="KEY")
    lookup = get_place_lookup(settings)
    assert isinstance(lookup, GoogleMapsPlaceLookup)


def test_get_place_lookup_requires_api_key_for_google():
    settings = _settings(place_lookup_provider="google", google_maps_api_key=None)
    with pytest.raises(ValueError, match="GOOGLE_MAPS_API_KEY"):
        get_place_lookup(settings)


def test_get_place_lookup_rejects_unknown_provider():
    settings = _settings(place_lookup_provider="bing")
    with pytest.raises(ValueError, match="Unknown PLACE_LOOKUP_PROVIDER"):
        get_place_lookup(settings)
