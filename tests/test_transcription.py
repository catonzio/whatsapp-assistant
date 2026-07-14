from unittest.mock import MagicMock, patch

import pytest

from whatsapp_assistant.services.transcription import TranscriptionService


def _make_service() -> tuple[TranscriptionService, MagicMock]:
    """Build a service with a mocked OpenAI client; return both."""
    with patch("whatsapp_assistant.services.transcription.OpenAI") as openai_cls:
        client = openai_cls.return_value
        client.audio.transcriptions.create.return_value = MagicMock(text="ciao mondo")
        service = TranscriptionService(api_key="sk-test", model="gpt-4o-transcribe")
    return service, client


async def test_transcribe_returns_text():
    service, client = _make_service()

    result = await service.transcribe(b"fake-audio", "audio/ogg")

    assert result == "ciao mondo"
    client.audio.transcriptions.create.assert_called_once()
    kwargs = client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-transcribe"


@pytest.mark.parametrize(
    ("mime", "expected_ext"),
    [
        ("audio/ogg", "ogg"),
        ("audio/mpeg", "mp3"),
        ("audio/mp4", "m4a"),
        ("audio/ogg; codecs=opus", "ogg"),  # parameters are stripped
        ("audio/unknown", "ogg"),  # falls back to ogg
    ],
)
async def test_transcribe_picks_extension_from_mime(mime, expected_ext):
    service, client = _make_service()

    await service.transcribe(b"fake-audio", mime)

    filename, content, content_type = (
        client.audio.transcriptions.create.call_args.kwargs["file"]
    )
    assert filename == f"audio.{expected_ext}"
    assert content == b"fake-audio"
    assert content_type == mime
