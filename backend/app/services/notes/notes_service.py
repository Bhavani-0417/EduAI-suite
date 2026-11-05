import os
import uuid
import io
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value
from fastapi import HTTPException, UploadFile, status

from app.models.notes import Note, NoteSource
from app.services.vault.encryption_service import encrypt_notes_text, decrypt_notes_text
from app.utils.note_upload_validation import (
    MAX_NOTE_UPLOAD_BYTES,
    validate_note_file_content,
    validate_note_upload,
)
from app.utils.file_storage import safe_filename_fragment
from app.utils.note_cloudinary import encode_authenticated_asset, destroy_authenticated_asset
from app.services.ai.chroma_service import (
    add_to_collection, search_collection, delete_from_collection
)
from app.services.ai.gemini_service import (
    classify_note, summarize_note, answer_question_with_context
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# TEXT EXTRACTION
# ─────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file using PyMuPDF"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def extract_text_from_image(file_bytes: bytes) -> str:
    """Extract text from image using Tesseract OCR"""
    try:
        import pytesseract
        from PIL import Image
        
        # Set Tesseract path for Windows
        pytesseract.pytesseract.tesseract_cmd = (
            r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        )
        
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"OCR extraction error: {e}")
        return ""


def extract_text(file_bytes: bytes, file_type: str) -> str:
    """Route to correct extractor based on file type"""
    if file_type == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif file_type in ["jpg", "jpeg", "png", "bmp", "tiff"]:
        return extract_text_from_image(file_bytes)
    else:
        return ""


# ─────────────────────────────────────────
# TEXT CHUNKING
# ─────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks for ChromaDB.
    
    Why chunks? 
    - Embedding models have token limits
    - Smaller chunks = more precise retrieval
    - Overlap ensures context isn't lost at boundaries
    
    Example with chunk_size=10, overlap=2:
    "Hello World Python Code Here"
    → ["Hello World", "World Python", "Python Code", "Code Here"]
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        if chunk.strip():  # skip empty chunks
            chunks.append(chunk)
        
        start += chunk_size - overlap
    
    return chunks


# ─────────────────────────────────────────
# CLOUDINARY UPLOAD (File Storage)
# ─────────────────────────────────────────

def upload_to_cloudinary(file_bytes: bytes, file_name: str, student_id: str) -> str:
    """
    Upload file to Cloudinary and return the URL.
    Cloudinary = cloud file storage (like Google Drive for our app)
    """
    try:
        import cloudinary
        import cloudinary.uploader
        from app.core.config import settings
        
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )
        
        # Upload to a folder named after student ID
        result = cloudinary.uploader.upload(
            file_bytes,
            folder=f"eduai/notes/{student_id}",
            public_id=f"{uuid.uuid4()}_{safe_filename_fragment(file_name.rsplit('.', 1)[0], 80)}",
            resource_type="auto",
            type="authenticated",
        )

        return encode_authenticated_asset(result)
    except Exception as exc:
        logger.exception("Authenticated Cloudinary note upload failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Private note storage is unavailable. Please try again.",
        ) from exc


# ─────────────────────────────────────────
# MAIN NOTE OPERATIONS
# ─────────────────────────────────────────

def upload_note(
    db: Session,
    student_id: str,
    file: UploadFile,
    source: str = "student"
) -> Note:
    """
    Complete note upload pipeline:
    1. Read file bytes
    2. Detect file type
    3. Upload to Cloudinary
    4. Extract text (OCR / PDF parser)
    5. AI classifies subject/topic
    6. AI generates summary
    7. Chunk text and store in ChromaDB
    8. Save note record to PostgreSQL
    """
    
    # Bound the read before parsing or sending the file to a cloud provider.
    file_name = file.filename or ""
    file_bytes = file.file.read(MAX_NOTE_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_NOTE_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Note uploads must be 10 MB or smaller.",
        )

    try:
        extension = validate_note_upload(file_name, len(file_bytes))
        validate_note_file_content(extension, file_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    note_id = str(uuid.uuid4())
    file_url = None
    chunks_indexed = False

    try:
        # Step 3 — Upload to private Cloudinary storage.
        logger.info("Uploading note file to authenticated Cloudinary delivery.")
        file_url = upload_to_cloudinary(file_bytes, file_name, student_id)

        # Step 4 — Extract text.
        extracted_text = extract_text(file_bytes, extension) or ""

        # Step 5 — AI classification and summary.
        classification = {"subject": None, "topic": None, "chapter": None}
        summary = None
        if extracted_text:
            classification = classify_note(extracted_text)
            summary = summarize_note(extracted_text)

            # Step 6 — Index plaintext only in process memory; Chroma persists
            # ciphertext documents plus vectors and a non-sensitive note ID.
            chunks = chunk_text(extracted_text)
            if chunks:
                add_to_collection(
                    student_id=student_id,
                    note_id=note_id,
                    chunks=chunks,
                    metadata={},
                )
                chunks_indexed = True

        # Step 7 — Persist all free-text note fields encrypted.
        note = Note(
            id=note_id,
            student_id=student_id,
            subject=encrypt_notes_text(classification.get("subject")),
            topic=encrypt_notes_text(classification.get("topic")),
            chapter=encrypt_notes_text(classification.get("chapter")),
            file_url=file_url,
            file_name=encrypt_notes_text(file_name),
            file_type=extension,
            extracted_text=encrypt_notes_text(extracted_text[:5000] if extracted_text else None),
            summary=encrypt_notes_text(summary),
            source=NoteSource.STUDENT if source == "student" else NoteSource.FACULTY,
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        logger.info("Encrypted note saved: %s", note.id)
        return note
    except Exception:
        db.rollback()
        if chunks_indexed:
            try:
                delete_from_collection(student_id, note_id)
            except Exception:
                logger.exception("Could not remove incomplete Chroma note index %s.", note_id)
        if file_url:
            try:
                destroy_authenticated_asset(file_url)
            except Exception:
                logger.exception("Could not remove incomplete private Cloudinary asset for note %s.", note_id)
        raise


def get_notes(
    db: Session,
    student_id: str,
    subject: str = None,
) -> list:
    """Load only the caller's notes, then decrypt/filter fields in process memory."""
    notes = (
        db.query(Note)
        .filter(Note.student_id == student_id)
        .order_by(Note.created_at.desc())
        .all()
    )
    visible_notes = []
    normalized_filter = subject.strip().casefold() if subject else None
    for note in notes:
        set_committed_value(note, "file_name", decrypt_notes_text(note.file_name))
        set_committed_value(note, "subject", decrypt_notes_text(note.subject))
        set_committed_value(note, "topic", decrypt_notes_text(note.topic))
        set_committed_value(note, "chapter", decrypt_notes_text(note.chapter))
        set_committed_value(note, "extracted_text", decrypt_notes_text(note.extracted_text))
        set_committed_value(note, "summary", decrypt_notes_text(note.summary))
        if normalized_filter and normalized_filter not in (note.subject or "").casefold():
            continue
        visible_notes.append(note)
    return visible_notes


def ask_question(
    db: Session,
    student_id: str,
    question: str,
    subject_filter: str = None,
) -> dict:
    """Retrieve encrypted-at-rest note chunks and answer from owner-scoped context."""
    results = search_collection(
        student_id=student_id,
        query=question,
        n_results=50 if subject_filter else 5,
    )

    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []
    note_ids = {
        meta.get("note_id")
        for meta in metadatas
        if isinstance(meta, dict) and meta.get("note_id")
    }
    if not note_ids:
        answer = answer_question_with_context(question, [])
        return {"question": question, "answer": answer, "sources": []}

    owned_notes = db.query(Note).filter(
        Note.student_id == student_id,
        Note.id.in_(note_ids),
    ).all()
    note_map = {}
    for note in owned_notes:
        note_map[note.id] = {
            "subject": decrypt_notes_text(note.subject) or "Unknown",
            "file_name": decrypt_notes_text(note.file_name) or "Unknown",
        }

    normalized_filter = subject_filter.strip().casefold() if subject_filter else None
    context_chunks = []
    sources = []
    seen = set()
    for chunk, meta in zip(documents, metadatas):
        note_id = meta.get("note_id") if isinstance(meta, dict) else None
        note_info = note_map.get(note_id)
        if not note_info:
            continue
        if normalized_filter and normalized_filter not in note_info["subject"].casefold():
            continue
        context_chunks.append(chunk)
        source = f"{note_info['subject']} - {note_info['file_name']}"
        if source not in seen:
            sources.append(source)
            seen.add(source)
        if len(context_chunks) >= 5:
            break

    answer = answer_question_with_context(question, context_chunks)
    return {"question": question, "answer": answer, "sources": sources}
