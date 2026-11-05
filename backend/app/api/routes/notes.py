from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.db.database import get_db
from app.schemas.notes_schema import AskQuestionRequest
from app.services.notes.notes_service import upload_note, get_notes, ask_question
from app.utils.note_cloudinary import resolve_note_asset_url
from app.services.vault.encryption_service import decrypt_notes_text
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/notes",
    tags=["Notes"]
)


@router.post("/upload", status_code=201)
def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a note file (PDF or image).
    
    POST /api/notes/upload
    Body: multipart/form-data with 'file' field
    
    Pipeline:
    1. Save file to Cloudinary
    2. Extract text (OCR/PDF)
    3. AI classifies subject/topic
    4. Store in ChromaDB
    5. Save metadata to PostgreSQL
    """
    note = upload_note(db, current_user.id, file)
    
    return {
        "message": "Note uploaded successfully!",
        "id": note.id,
        "file_name": decrypt_notes_text(note.file_name),
        "subject": decrypt_notes_text(note.subject),
        "topic": decrypt_notes_text(note.topic),
        "chapter": decrypt_notes_text(note.chapter),
        "summary": decrypt_notes_text(note.summary),
        "file_url": resolve_note_asset_url(note.file_url, note.file_type),
        "created_at": str(note.created_at)
    }


@router.get("/")
def list_notes(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notes for logged-in student.
    Optionally filter by subject name.
    """
    notes = get_notes(db, current_user.id, subject)
    
    result = []
    for note in notes:
        result.append({
            "id": note.id,
            "subject": decrypt_notes_text(note.subject),
            "topic": decrypt_notes_text(note.topic),
            "chapter": decrypt_notes_text(note.chapter),
            "file_name": decrypt_notes_text(note.file_name),
            "file_type": note.file_type,
            "file_url": resolve_note_asset_url(note.file_url, note.file_type),
            "summary": decrypt_notes_text(note.summary),
            "source": note.source.value if note.source else "student",
            "created_at": str(note.created_at)
        })
    
    return {"total": len(result), "notes": result}


@router.post("/ask")
def ask(
    request: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ask a question about your notes (RAG).
    
    POST /api/notes/ask
    Body: { question, subject (optional) }
    
    AI searches your uploaded notes and answers from them.
    """
    return ask_question(
        db=db,
        student_id=current_user.id,
        question=request.question,
        subject_filter=request.subject
    )


@router.delete("/{note_id}")
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a note and remove from ChromaDB"""
    from app.models.notes import Note
    
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.student_id == current_user.id
    ).first()
    
    if not note:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found."
        )
    
    # Remove from ChromaDB
    delete_from_collection(current_user.id, note_id)
    
    # Remove from PostgreSQL
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully."}