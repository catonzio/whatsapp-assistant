import pytest


def _audio_payload(media_id: str = "MEDIA123", sender: str = "393331112222") -> dict:
    """A minimal WhatsApp webhook payload carrying one audio message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": sender,
                                    "id": "wamid.ABC",
                                    "type": "audio",
                                    "audio": {"id": media_id, "mime_type": "audio/ogg"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


@pytest.fixture
def audio_payload() -> dict:
    return _audio_payload()


@pytest.fixture
def text_payload() -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "393331112222",
                                    "id": "wamid.TXT",
                                    "type": "text",
                                    "text": {"body": "ciao"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
