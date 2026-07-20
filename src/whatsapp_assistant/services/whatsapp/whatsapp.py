import logging

import httpx

logger = logging.getLogger("whatsapp-assistant")


class WhatsAppClient:
    """Low-level client for the WhatsApp Cloud API (Graph API)."""

    def __init__(self, token: str, phone_number_id: str, graph_url: str) -> None:
        self._token = token
        self._phone_number_id = phone_number_id
        self._graph_url = graph_url

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def download_media(self, media_id: str) -> tuple[bytes, str]:
        """WhatsApp media download is two steps: resolve the media ID to a temporary
        URL, then fetch the bytes. Both requests need the access token."""
        async with httpx.AsyncClient(timeout=30) as http:
            meta_resp = await http.get(
                f"{self._graph_url}/{media_id}", headers=self._auth_headers()
            )
            meta_resp.raise_for_status()
            info = meta_resp.json()

            media_resp = await http.get(info["url"], headers=self._auth_headers())
            media_resp.raise_for_status()
            return media_resp.content, info.get("mime_type", "audio/ogg")

    async def send_text(self, to: str, body: str) -> None:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.post(
                f"{self._graph_url}/{self._phone_number_id}/messages",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": body},
                },
            )
            if resp.is_error:
                logger.error(
                    "Failed to send message: %s %s", resp.status_code, resp.text
                )
            resp.raise_for_status()
