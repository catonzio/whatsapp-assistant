import httpx
import pytest
import respx

from whatsapp_assistant.services.whatsapp.whatsapp import WhatsAppClient

GRAPH_URL = "https://graph.facebook.com/v21.0"


@pytest.fixture
def client() -> WhatsAppClient:
    return WhatsAppClient(
        token="TOKEN",
        phone_number_id="PHONE123",
        graph_url=GRAPH_URL,
    )


@respx.mock
async def test_download_media_two_step(client: WhatsAppClient):
    media_id = "MEDIA123"
    media_url = "https://lookaside.fbsbx.com/media/xyz"

    meta_route = respx.get(f"{GRAPH_URL}/{media_id}").mock(
        return_value=httpx.Response(
            200, json={"url": media_url, "mime_type": "audio/ogg"}
        )
    )
    bytes_route = respx.get(media_url).mock(
        return_value=httpx.Response(200, content=b"OGG-BYTES")
    )

    content, mime = await client.download_media(media_id)

    assert content == b"OGG-BYTES"
    assert mime == "audio/ogg"
    # Both requests must carry the bearer token.
    assert meta_route.calls.last.request.headers["Authorization"] == "Bearer TOKEN"
    assert bytes_route.calls.last.request.headers["Authorization"] == "Bearer TOKEN"


@respx.mock
async def test_download_media_defaults_mime_when_missing(client: WhatsAppClient):
    media_url = "https://lookaside.fbsbx.com/media/xyz"
    respx.get(f"{GRAPH_URL}/MEDIA123").mock(
        return_value=httpx.Response(200, json={"url": media_url})
    )
    respx.get(media_url).mock(return_value=httpx.Response(200, content=b"data"))

    _, mime = await client.download_media("MEDIA123")

    assert mime == "audio/ogg"


@respx.mock
async def test_send_text_posts_expected_body(client: WhatsAppClient):
    route = respx.post(f"{GRAPH_URL}/PHONE123/messages").mock(
        return_value=httpx.Response(200, json={"messages": [{"id": "wamid.OUT"}]})
    )

    await client.send_text("393331112222", "trascrizione")

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer TOKEN"
    import json

    body = json.loads(request.content)
    assert body == {
        "messaging_product": "whatsapp",
        "to": "393331112222",
        "type": "text",
        "text": {"body": "trascrizione"},
    }


@respx.mock
async def test_send_text_raises_on_error(client: WhatsAppClient):
    respx.post(f"{GRAPH_URL}/PHONE123/messages").mock(
        return_value=httpx.Response(400, json={"error": {"message": "bad"}})
    )

    with pytest.raises(httpx.HTTPStatusError):
        await client.send_text("393331112222", "x")
