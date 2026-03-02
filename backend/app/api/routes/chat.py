import os
from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.ai.chat_agent import run_chat_agent
from app.services.ai.voice_service import speech_to_text, text_to_speech
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/chat",
    tags=["AI Chatbot"]
)


@router.post("/message", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    include_audio: bool = Query(False, description="Return TTS audio with response"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Main chat endpoint — text in, AI reply out.

    POST /api/chat/message
    Body: {
        message: "What is normalization?",
        mode: "auto",           ← auto / notes / general
        subject: "DBMS",        ← optional, filters notes search
        conversation_history: [] ← send previous messages for memory
    }

    Modes:
    - auto    → LangGraph decides notes vs general
    - notes   → Always search uploaded notes first
    - general → Always use Gemini general knowledge
    """
    result = run_chat_agent(
        student_id=current_user.id,
        user_message=request.message,
        mode=request.mode.value,
        subject_filter=request.subject,
        conversation_history=[
            msg.model_dump()
            for msg in request.conversation_history
        ]
    )

    # Generate TTS audio if requested
    audio_url = None
    if include_audio:
        audio_file = text_to_speech(result["message"])
        if audio_file:
            audio_url = f"/api/chat/audio/{audio_file}"

    return ChatResponse(
        message=result["message"],
        mode_used=result["mode_used"],
        sources=result.get("sources", []),
        audio_url=audio_url
    )


@router.post("/voice")
def voice_chat(
    file: UploadFile = File(...),
    mode: str = Query("auto"),
    subject: Optional[str] = Query(None),
    include_audio: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Voice chat endpoint — audio in, AI reply out.

    POST /api/chat/voice
    Body: audio file (wav, mp3, m4a, webm)

    Flow:
    1. faster-whisper transcribes audio → text
    2. LangGraph agent processes text
    3. gTTS converts reply to audio
    4. Returns both text + audio URL
    """

    # Read audio bytes
    audio_bytes = file.file.read()
    file_ext = file.filename.split(".")[-1].lower()

    # Step 1 — Speech to Text
    transcribed = speech_to_text(audio_bytes, file_ext)

    if not transcribed:
        return {
            "error": "Could not understand audio. Please speak clearly and try again.",
            "transcribed_text": "",
            "ai_reply": "",
            "audio_url": None
        }

    # Step 2 — Run chat agent with transcribed text
    result = run_chat_agent(
        student_id=current_user.id,
        user_message=transcribed,
        mode=mode,
        subject_filter=subject,
        conversation_history=[]
    )

    # Step 3 — TTS response
    audio_url = None
    if include_audio:
        audio_file = text_to_speech(result["message"])
        if audio_file:
            audio_url = f"/api/chat/audio/{audio_file}"

    return {
        "transcribed_text": transcribed,
        "ai_reply": result["message"],
        "mode_used": result["mode_used"],
        "sources": result.get("sources", []),
        "audio_url": audio_url
    }


@router.get("/audio/{file_name}")
def get_audio(
    file_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download/stream a TTS audio file.

    GET /api/chat/audio/{file_name}
    Returns MP3 audio file.
    """
    file_path = os.path.join("generated_files", file_name)

    if not os.path.exists(file_path):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found."
        )

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=file_name
    )


@router.get("/history/clear")
def clear_history_info():
    """
    Chat history is managed client-side.
    Frontend sends conversation_history with each request.
    This endpoint explains that.
    """
    return {
        "info": "Chat history is managed by the frontend.",
        "how": "Send previous messages in the conversation_history field of each request.",
        "example": {
            "message": "Explain it more simply",
            "conversation_history": [
                {"role": "user", "content": "What is normalization?"},
                {"role": "assistant", "content": "Normalization is..."}
            ]
        }
    }