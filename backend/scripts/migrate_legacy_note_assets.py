"""Convert legacy public Cloudinary note assets to authenticated delivery.

Run from backend/:
    python -m scripts.migrate_legacy_note_assets                 # inventory only
    python -m scripts.migrate_legacy_note_assets --apply          # prompts for confirmation

Back up PostgreSQL and retain a Cloudinary asset inventory before applying.
The script converts one asset at a time using Cloudinary's rename API with
to_type='authenticated' and invalidate=True, then stores a versioned locator.
"""

import argparse
import logging

import cloudinary
import cloudinary.api
import cloudinary.uploader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.notes import Note
from app.utils.note_cloudinary import (
    CLOUDINARY_AUTH_REF_PREFIX,
    encode_authenticated_asset,
    parse_legacy_cloudinary_upload_url,
)

logger = logging.getLogger("legacy-note-assets")


def parse_legacy_upload_url(url: str) -> dict[str, str] | None:
    """Compatibility wrapper around the tested Cloudinary URL parser."""
    return parse_legacy_cloudinary_upload_url(url)

def _resource(public_id: str, resource_type: str, delivery_type: str) -> dict | None:
    try:
        return cloudinary.api.resource(
            public_id,
            resource_type=resource_type,
            type=delivery_type,
        )
    except Exception:
        return None


def convert_asset(public_url: str) -> str:
    """Convert or recover an already-converted legacy asset and return its locator."""
    parsed = parse_legacy_upload_url(public_url)
    if not parsed:
        raise ValueError("Unsupported or non-direct legacy Cloudinary URL.")

    public_id = parsed["public_id"]
    resource_type = parsed["resource_type"]
    existing = _resource(public_id, resource_type, "authenticated")
    if existing:
        asset = existing
    else:
        asset = _resource(public_id, resource_type, "upload")
        if not asset:
            raise RuntimeError(f"Cloudinary asset not found: {public_id}")
        cloudinary.uploader.rename(
            public_id,
            public_id,
            resource_type=resource_type,
            type="upload",
            to_type="authenticated",
            invalidate=True,
            overwrite=False,
        )
        asset = _resource(public_id, resource_type, "authenticated") or asset

    payload = {
        "public_id": public_id,
        "resource_type": resource_type,
        "format": asset.get("format") or parsed["format"],
        "type": "authenticated",
    }
    return encode_authenticated_asset(payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate old public note assets.")
    parser.add_argument("--apply", action="store_true", help="Convert assets and update PostgreSQL.")
    args = parser.parse_args()

    db: Session = SessionLocal()
    try:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )
        notes = db.query(Note).all()
        candidates = [
            note for note in notes
            if note.file_url and not note.file_url.startswith(CLOUDINARY_AUTH_REF_PREFIX)
        ]
        logger.info("Legacy note URLs found: %d", len(candidates))
        if not args.apply:
            for note in candidates:
                parsed = parse_legacy_upload_url(note.file_url)
                logger.info(
                    "Note %s: %s",
                    note.id,
                    "convertible Cloudinary URL" if parsed else "unsupported URL (manual review required)",
                )
            logger.info("Inventory only: no Cloudinary assets or database rows were changed.")
            return

        confirmation = input("Type MIGRATE LEGACY NOTE ASSETS to continue: ").strip()
        if confirmation != "MIGRATE LEGACY NOTE ASSETS":
            logger.warning("Confirmation did not match; no assets were changed.")
            return

        migrated = 0
        failed = 0
        for note in candidates:
            try:
                note.file_url = convert_asset(note.file_url)
                db.commit()
                migrated += 1
            except Exception:
                db.rollback()
                failed += 1
                logger.exception("Could not migrate note asset %s.", note.id)
        logger.info("Legacy Cloudinary conversion complete: migrated=%d failed=%d", migrated, failed)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
