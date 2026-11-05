"""Encode Cloudinary authenticated-asset references and mint short-lived URLs."""

import json
import time
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

CLOUDINARY_AUTH_REF_PREFIX = "cloudinary-auth:v1:"


def encode_authenticated_asset(upload_result: dict[str, Any]) -> str:
    """Store only the Cloudinary locator, never a public CDN URL."""
    required = ("public_id", "resource_type", "format")
    if any(not upload_result.get(key) for key in required):
        raise ValueError("Cloudinary upload response is missing asset metadata.")

    payload = {
        "public_id": upload_result["public_id"],
        "resource_type": upload_result["resource_type"],
        "format": upload_result["format"],
        "type": "authenticated",
    }
    return CLOUDINARY_AUTH_REF_PREFIX + json.dumps(
        payload, separators=(",", ":"), sort_keys=True
    )


def decode_authenticated_asset(stored_value: str) -> dict[str, str] | None:
    """Decode our versioned locator; return None for legacy non-marker URLs."""
    if not isinstance(stored_value, str) or not stored_value.startswith(CLOUDINARY_AUTH_REF_PREFIX):
        return None

    raw = stored_value[len(CLOUDINARY_AUTH_REF_PREFIX):]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Stored Cloudinary asset reference is invalid.") from exc

    if (
        not isinstance(payload, dict)
        or not all(isinstance(payload.get(key), str) and payload[key] for key in ("public_id", "resource_type", "format"))
        or payload.get("type") != "authenticated"
    ):
        raise ValueError("Stored Cloudinary asset reference is incomplete.")
    return payload


def resolve_note_asset_url(
    stored_value: str,
    legacy_file_type: str | None = None,
    *,
    private_download_url: Callable[..., str] | None = None,
    now: int | None = None,
    expires_in_seconds: int = 900,
) -> str | None:
    """
    Create an expiring signed URL for authenticated Cloudinary media.

    Legacy public URLs are intentionally not returned by the API. Those assets
    remain publicly accessible at Cloudinary until explicitly migrated there.
    """
    asset = decode_authenticated_asset(stored_value)
    if asset is None:
        return None

    if expires_in_seconds < 60 or expires_in_seconds > 3600:
        raise ValueError("Signed note URL expiry must be between 60 and 3600 seconds.")

    if private_download_url is None:
        import cloudinary
        from app.core.config import settings
        from cloudinary.utils import private_download_url as sdk_private_download_url

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        private_download_url = sdk_private_download_url

    expires_at = (int(time.time()) if now is None else int(now)) + expires_in_seconds
    file_format = asset.get("format") or legacy_file_type
    if not file_format:
        raise ValueError("Cloudinary note asset has no file format.")

    return private_download_url(
        asset["public_id"],
        file_format,
        resource_type=asset["resource_type"],
        type="authenticated",
        expires_at=expires_at,
    )



def destroy_authenticated_asset(
    stored_value: str,
    *,
    destroy_asset: Callable[..., dict] | None = None,
) -> bool:
    """Best-effort cleanup for a just-uploaded private asset after DB/Chroma failure."""
    asset = decode_authenticated_asset(stored_value)
    if asset is None:
        return False
    if destroy_asset is None:
        import cloudinary
        import cloudinary.uploader
        from app.core.config import settings

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        destroy_asset = cloudinary.uploader.destroy
    result = destroy_asset(
        asset["public_id"],
        resource_type=asset["resource_type"],
        type="authenticated",
        invalidate=True,
    )
    return result.get("result") in {"ok", "not found"}
