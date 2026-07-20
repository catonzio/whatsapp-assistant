"""Verification of Meta's webhook payload signature.

WhatsApp Cloud API signs every webhook POST body with the app secret
(HMAC-SHA256, header `X-Hub-Signature-256: sha256=<hex>`). Without checking
it, anyone who learns the webhook URL can POST a fabricated payload and have
it processed as if it came from a real user — see docs/architecture.md §2.
"""

import hashlib
import hmac


def verify_signature(body: bytes, signature_header: str | None, app_secret: str) -> bool:
    """Return True if `signature_header` is a valid HMAC-SHA256 of `body` keyed with `app_secret`."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, provided)
