import os
from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.schemas.chat_schema import ChatRequest, ChatResponse, ChatMode
from app.services.ai.chat_agent import run_chat_agent
from app.services.ai.voice_service import speech_to_text, text_to_speech
from app.api.middlewares.auth_middleware import get_current_user
from app.models.user import User
from app.utils.file_storage import resolve_generated_file

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot"])


@router.post("/message", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    include_audio: bool = Query(False, description="Return TTS audio with response"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = run_chat_agent(
        student_id=current_user.id,
        user_message=request.message,
        mode=request.mode.value,
        subject_filter=request.subject,
        conversation_history=[
            msg.model_dump() for msg in request.conversation_history
        ],
    )
    audio_url = None
    if include_audio:
        audio_file = text_to_speech(result["message"])
        if audio_file:
            audio_url = f"/api/chat/audio/{audio_file}"

    return ChatResponse(
        message=result["message"],
        mode_used=result["mode_used"],
        sources=result.get("sources", []),
        audio_url=audio_url,
    )


@router.post("/voice")
def voice_chat(
    file: UploadFile = File(...),
    mode: ChatMode = Query(ChatMode.AUTO),
    subject: Optional[str] = Query(None),
    include_audio: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_name = (file.filename or "").replace("\\", "/").split("/")[-1]
    file_ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if file_ext not in {"wav", "mp3", "m4a", "webm"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload WAV, MP3, M4A, or WebM audio.",
        )

    max_audio_bytes = 15 * 1024 * 1024
    audio_bytes = file.file.read(max_audio_bytes + 1)
    if len(audio_bytes) > max_audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio uploads must be 15 MB or smaller.",
        )
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The audio upload is empty.",
        )

    transcribed = speech_to_text(audio_bytes, file_ext)
    if not transcribed:
        return {
            "error": "Could not understand audio. Please speak clearly and try again.",
            "transcribed_text": "",
            "ai_reply": "",
            "audio_url": None,
        }

    result = run_chat_agent(
        student_id=current_user.id,
        user_message=transcribed,
        mode=mode.value,
        subject_filter=subject,
        conversation_history=[],
    )
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
        "audio_url": audio_url,
    }


@router.get("/audio/{file_name}")
def get_audio(
    file_name: str,
    current_user: User = Depends(get_current_user),
):
    try:
        file_path = resolve_generated_file(file_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name.",
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found.",
        ) from exc

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=file_name,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


@router.get("/history/clear")
def clear_history_info():
    """Explain that the client supplies chat history with each request."""
    return {
        "info": "Chat history is managed by the frontend.",
        "how": "Send previous messages in the conversation_history field of each request.",
        "example": {
            "message": "Explain it more simply",
            "conversation_history": [
                {"role": "user", "content": "What is normalization?"},
                {"role": "assistant", "content": "Normalization is..."},
            ],
        },
    }
