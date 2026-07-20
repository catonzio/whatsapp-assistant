from dataclasses import dataclass, field


@dataclass
class Attachment:
    """Interface-agnostic attachment (audio, photo, ...) passed to a ChatService."""

    filename: str
    data: bytes
    mime_type: str


@dataclass
class ChatMessage:
    """Interface-agnostic message passed to a ChatService.

    `session_id`: optional on purpose. WhatsApp (and the CLI, by default)
    have no notion of "starting a new conversation" — there's a single,
    continuous thread per user. When left as None, concrete implementations
    resolve it deterministically from `user_id` (one ongoing session per
    user). Pass an explicit value only to address a specific session
    (e.g. CLI testing with multiple simulated users/threads).
    """

    user_id: str
    text: str
    session_id: str | None = None
    attachments: list[Attachment] = field(default_factory=list)
