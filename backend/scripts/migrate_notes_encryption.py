"""Encrypt legacy note content and ChromaDB documents in place.

Run from backend/:
    python -m scripts.migrate_notes_encryption          # dry run
    python -m scripts.migrate_notes_encryption --apply

Back up PostgreSQL and CHROMA_PERSIST_DIR before using --apply.
Existing Chroma embeddings are retained exactly; no re-embedding is performed.
"""

import argparse
import logging
from collections import defaultdict

from app.db.database import SessionLocal
from app.models.notes import Note
from app.services.ai.chroma_service import get_chroma_client
from app.services.vault.encryption_service import (
    NOTES_CIPHERTEXT_PREFIX,
    decrypt_notes_text,
    encrypt_notes_text,
)

logger = logging.getLogger("notes-encryption-migration")
NOTE_TEXT_FIELDS = (
    "file_name",
    "subject",
    "topic",
    "chapter",
    "extracted_text",
    "summary",
)
BATCH_SIZE = 250


def _note_lookup(notes: list[Note]) -> tuple[dict[str, dict[str, list[str]]], dict[str, str]]:
    """Build collection-owner and unique owner+filename lookup before encrypting names."""
    by_owner_and_name: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    collection_owners: dict[str, str] = {}
    for note in notes:
        old_name = decrypt_notes_text(note.file_name) or ""
        if old_name:
            by_owner_and_name[note.student_id][old_name].append(note.id)
        collection_owners[f"student_{note.student_id.replace('-', '_')}"] = note.student_id
    return by_owner_and_name, collection_owners


def migrate_note_rows(db, notes: list[Note], apply: bool) -> int:
    changed = 0
    for note in notes:
        for field in NOTE_TEXT_FIELDS:
            stored = getattr(note, field)
            if stored and not stored.startswith(NOTES_CIPHERTEXT_PREFIX):
                changed += 1
                if apply:
                    setattr(note, field, encrypt_notes_text(stored))
        if apply and changed and changed % 100 == 0:
            db.commit()
    if apply:
        db.commit()
    return changed


def migrate_chroma_collection(
    collection,
    student_id: str,
    owner_filename_map: dict[str, dict[str, list[str]]],
    apply: bool,
) -> tuple[int, int]:
    """Encrypt document strings while preserving existing embeddings and IDs."""
    migrated = 0
    unmapped = 0
    offset = 0
    filename_map = owner_filename_map.get(student_id, {})

    while True:
        page = collection.get(
            limit=BATCH_SIZE,
            offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )
        ids = page.get("ids") or []
        if not ids:
            break

        documents = page.get("documents") or [None] * len(ids)
        metadatas = page.get("metadatas") or [{} for _ in ids]
        embeddings = page.get("embeddings")
        if embeddings is None:
            raise RuntimeError(
                f"Collection {collection.name} returned no embeddings; refusing to re-embed."
            )

        encrypted_documents = []
        safe_metadatas = []
        page_migrated = 0
        for document, metadata in zip(documents, metadatas):
            metadata = metadata or {}
            note_id = metadata.get("note_id")
            if not note_id:
                legacy_file_name = metadata.get("file_name")
                candidates = filename_map.get(legacy_file_name, []) if legacy_file_name else []
                if len(candidates) == 1:
                    note_id = candidates[0]
                else:
                    unmapped += 1

            clean_metadata = {"note_id": note_id} if note_id else {"legacy_unmapped": True}
            if document and not document.startswith(NOTES_CIPHERTEXT_PREFIX):
                document = encrypt_notes_text(document)
                page_migrated += 1
            encrypted_documents.append(document)
            safe_metadatas.append(clean_metadata)

        if apply and page_migrated:
            vectors = embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings
            collection.update(
                ids=ids,
                embeddings=vectors,
                documents=encrypted_documents,
                metadatas=safe_metadatas,
            )
        elif apply and safe_metadatas != metadatas:
            vectors = embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings
            collection.update(
                ids=ids,
                embeddings=vectors,
                documents=encrypted_documents,
                metadatas=safe_metadatas,
            )

        migrated += page_migrated
        offset += len(ids)
        if len(ids) < BATCH_SIZE:
            break

    return migrated, unmapped


def main() -> None:
    parser = argparse.ArgumentParser(description="Encrypt legacy EduAI note data.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write encrypted PostgreSQL and ChromaDB values. Default is dry-run.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        notes = db.query(Note).all()
        owner_filename_map, collection_owners = _note_lookup(notes)
        fields_to_encrypt = sum(
            1
            for note in notes
            for field in NOTE_TEXT_FIELDS
            if (value := getattr(note, field))
            and not value.startswith(NOTES_CIPHERTEXT_PREFIX)
        )
        logger.info(
            "Notes to inspect: %d; PostgreSQL text fields to encrypt: %d",
            len(notes),
            fields_to_encrypt,
        )

        if args.apply:
            migrate_note_rows(db, notes, apply=True)

        client = get_chroma_client()
        total_chunks = 0
        total_unmapped = 0
        for listed_collection in client.list_collections():
            collection_name = listed_collection.name if hasattr(listed_collection, "name") else str(listed_collection)
            student_id = collection_owners.get(collection_name)
            if not student_id and collection_name.startswith("student_"):
                # Encrypt orphaned collections too; without an owner row their
                # chunks are deliberately marked unlinked and excluded from RAG.
                student_id = collection_name.removeprefix("student_").replace("_", "-")
                owner_filename_map.setdefault(student_id, {})
            if not student_id:
                logger.warning("Skipping non-student Chroma collection: %s", collection_name)
                continue
            collection = client.get_collection(name=collection_name)
            chunks, unmapped = migrate_chroma_collection(
                collection,
                student_id,
                owner_filename_map,
                apply=args.apply,
            )
            total_chunks += chunks
            total_unmapped += unmapped

        mode = "Applied" if args.apply else "Dry run:"
        logger.info(
            "%s PostgreSQL text fields=%d; Chroma documents=%d; unmapped legacy chunks=%d",
            mode,
            fields_to_encrypt,
            total_chunks,
            total_unmapped,
        )
        if total_unmapped:
            logger.warning(
                "Some legacy Chroma chunks could not be uniquely associated with a note. "
                "Their text was encrypted, but they have no note_id and cannot be individually deleted."
            )
        if not args.apply:
            logger.info("No data changed. Re-run with --apply only after backups.")
    except Exception:
        db.rollback()
        logger.exception("Notes encryption migration failed.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
