import os
import uuid
import io
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status

from app.models.notes import Note, NoteSource
from app.services.ai.chroma_service import (
    add_to_collection, search_collection, delete_from_collection
)
from app.services.ai.gemini_service import (
    classify_note, summarize_note, answer_question_with_context
)


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
            public_id=f"{uuid.uuid4()}_{file_name}",
            resource_type="auto"
        )
        
        return result["secure_url"]
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        # Return placeholder if Cloudinary not configured
        return f"local://{student_id}/{file_name}"


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
    
    # Step 1 — Read file
    file_bytes = file.file.read()
    file_name = file.filename
    
    # Step 2 — Detect file type
    extension = file_name.split(".")[-1].lower()
    allowed_types = ["pdf", "jpg", "jpeg", "png", "bmp", "tiff"]
    if extension not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{extension} not supported. Use: {', '.join(allowed_types)}"
        )
    
    # Step 3 — Upload to Cloudinary
    print(f"📤 Uploading {file_name} to Cloudinary...")
    file_url = upload_to_cloudinary(file_bytes, file_name, student_id)
    
    # Step 4 — Extract text
    print(f"📝 Extracting text from {extension} file...")
    extracted_text = extract_text(file_bytes, extension)
    
    if not extracted_text:
        print("⚠️ No text extracted — file may be image-only or empty")
        extracted_text = ""
    
    # Step 5 — AI classifies subject and topic
    classification = {"subject": None, "topic": None, "chapter": None}
    summary = None
    
    if extracted_text:
        print("🤖 Classifying subject and topic with AI...")
        classification = classify_note(extracted_text)
        
        # Step 6 — Generate summary
        print("📋 Generating summary with AI...")
        summary = summarize_note(extracted_text)
        
        # Step 7 — Chunk and store in ChromaDB
        print("🧠 Storing in vector database...")
        chunks = chunk_text(extracted_text)
        
        if chunks:
            add_to_collection(
                student_id=student_id,
                note_id=str(uuid.uuid4()),
                chunks=chunks,
                metadata={
                    "subject": classification.get("subject") or "Unknown",
                    "topic": classification.get("topic") or "Unknown",
                    "file_name": file_name,
                    "source": source
                }
            )
    
    # Step 8 — Save to PostgreSQL
    note = Note(
        id=str(uuid.uuid4()),
        student_id=student_id,
        subject=classification.get("subject"),
        topic=classification.get("topic"),
        chapter=classification.get("chapter"),
        file_url=file_url,
        file_name=file_name,
        file_type=extension,
        extracted_text=extracted_text[:5000] if extracted_text else None,
        summary=summary,
        source=NoteSource.STUDENT if source == "student" else NoteSource.FACULTY
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    print(f"✅ Note saved: {note.id}")
    return note


def get_notes(
    db: Session,
    student_id: str,
    subject: str = None
) -> list:
    """Get all notes for a student, optionally filtered by subject"""
    query = db.query(Note).filter(Note.student_id == student_id)
    
    if subject:
        query = query.filter(Note.subject.ilike(f"%{subject}%"))
    
    return query.order_by(Note.created_at.desc()).all()


def ask_question(
    db: Session,
    student_id: str,
    question: str,
    subject_filter: str = None
) -> dict:
    """
    RAG Pipeline — Answer a question from student's notes.
    
    Retrieval → Augmentation → Generation
    """
    # RETRIEVAL — search ChromaDB for relevant chunks
    print(f"🔍 Searching notes for: {question}")
    results = search_collection(
        student_id=student_id,
        query=question,
        n_results=5,
        subject_filter=subject_filter
    )
    
    # Extract relevant chunks and source info
    context_chunks = []
    sources = []
    
    if results["documents"] and results["documents"][0]:
        context_chunks = results["documents"][0]
        
        if results["metadatas"] and results["metadatas"][0]:
            for meta in results["metadatas"][0]:
                source = f"{meta.get('subject', 'Unknown')} - {meta.get('file_name', 'Unknown')}"
                if source not in sources:
                    sources.append(source)
    
    # GENERATION — ask Gemini to answer using retrieved context
    print(f"🤖 Generating answer with {len(context_chunks)} context chunks...")
    answer = answer_question_with_context(question, context_chunks)
    
    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }