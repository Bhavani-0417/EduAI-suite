"""Small helpers for safely serving private vault files."""

from datetime import datetime, timezone
from urllib.parse import quote


def as_utc_datetime(value: datetime) -> datetime:
    """Normalize DB datetimes (including legacy naive values) to aware UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_share_expired(expires_at: datetime, now: datetime | None = None) -> bool:
    """Compare aware or legacy-naive database expiry values safely in UTC."""
    current_time = as_utc_datetime(now or datetime.now(timezone.utc))
    return current_time >= as_utc_datetime(expires_at)


def content_disposition_attachment(file_name: str | None) -> str:
    """
    Build a safe RFC 6266 Content-Disposition value.

    The fallback is deliberately static; the real UTF-8 filename is safely
    percent-encoded so CR/LF and quotes cannot inject response headers.
    """
    candidate = (file_name or "").replace("\\", "/").split("/")[-1]
    safe_name = "".join(
        char for char in candidate
        if ord(char) >= 32 and ord(char) != 127
    ).strip()
    if safe_name in {"", ".", ".."}:
        safe_name = "download"
    return (
        'attachment; filename="download"; '
        f"filename*=UTF-8''{quote(safe_name, safe='')}"
    )
