"""Link metadata fetch tool (docs/architecture.md §8.3, requirements.md §4.5).

Fetches a URL's og:title/og:description/og:image so a saved link carries
real context instead of a bare string. Whether this runs immediately or only
after the user confirms is a CatalogingAgent instruction decision driven by
`Settings.link_auto_fetch`, not something this function decides — it always
just fetches when called.
"""

from html.parser import HTMLParser

import httpx

from whatsapp_assistant.agents.wrappers import may_fail_async

_OG_PROPERTIES = {"og:title", "og:description", "og:image"}


class _OpenGraphParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.og: dict[str, str] = {}
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "meta":
            prop = attrs_dict.get("property") or attrs_dict.get("name")
            content = attrs_dict.get("content")
            if prop in _OG_PROPERTIES and content:
                self.og[prop] = content
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and self.title is None:
            self.title = data.strip()


@may_fail_async
async def fetch_link_metadata(url: str) -> dict:
    """Fetch a web page and extract its title/description/preview image.

    Args:
        url: the link to fetch, exactly as sent by the user.

    Returns:
        {"success": True, "title": str | None, "description": str | None,
         "image_url": str | None} — fields are None if not present on the page.
    """
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as http:
        resp = await http.get(url, headers={"User-Agent": "whatsapp-assistant/0.1"})
        resp.raise_for_status()
        html = resp.text

    parser = _OpenGraphParser()
    parser.feed(html)
    return {
        "success": True,
        "title": parser.og.get("og:title") or parser.title,
        "description": parser.og.get("og:description"),
        "image_url": parser.og.get("og:image"),
    }
