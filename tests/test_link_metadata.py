import httpx
import respx

from whatsapp_assistant.agents.tools.link_metadata import fetch_link_metadata

_HTML = """
<html>
<head>
<title>Fallback Title</title>
<meta property="og:title" content="Ristorante da Mario" />
<meta property="og:description" content="Cucina romana tradizionale" />
<meta property="og:image" content="https://example.com/photo.jpg" />
</head>
<body></body>
</html>
"""


@respx.mock
async def test_fetch_link_metadata_extracts_og_tags():
    respx.get("https://example.com/ristorante").mock(
        return_value=httpx.Response(200, text=_HTML)
    )

    result = await fetch_link_metadata("https://example.com/ristorante")

    assert result["success"] is True
    assert result["title"] == "Ristorante da Mario"
    assert result["description"] == "Cucina romana tradizionale"
    assert result["image_url"] == "https://example.com/photo.jpg"


@respx.mock
async def test_fetch_link_metadata_falls_back_to_title_tag():
    html = "<html><head><title>Solo titolo</title></head><body></body></html>"
    respx.get("https://example.com/no-og").mock(
        return_value=httpx.Response(200, text=html)
    )

    result = await fetch_link_metadata("https://example.com/no-og")

    assert result["success"] is True
    assert result["title"] == "Solo titolo"
    assert result["description"] is None


@respx.mock
async def test_fetch_link_metadata_reports_http_errors():
    respx.get("https://example.com/missing").mock(return_value=httpx.Response(404))

    result = await fetch_link_metadata("https://example.com/missing")

    assert result["success"] is False
    assert "error" in result
