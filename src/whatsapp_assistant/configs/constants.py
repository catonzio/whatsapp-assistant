import re

# Allowed MIME types for attachments (photos and videos only)
ALLOWED_MIME_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
}

SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]")
