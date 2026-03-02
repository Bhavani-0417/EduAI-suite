from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class ChatMode(str, Enum):
    GENERAL = "general"       # answer from Gemini general knowledge
    NOTES = "notes"           # answer only from uploaded notes
    AUTO = "auto"             # LangGraph decides automatically


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Single message in conversation"""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """Request body for chat endpoint"""
    message: str
    mode: ChatMode = ChatMode.AUTO
    subject: Optional[str] = None            # filter notes by subject
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    """Response from chatbot"""
    message: str                              # AI reply text
    mode_used: str                            # which mode was actually used
    sources: Optional[List[str]] = []         # notes used (if RAG mode)
    audio_url: Optional[str] = None           # TTS audio file URL


class VoiceResponse(BaseModel):
    """Response from voice endpoint"""
    transcribed_text: str                     # what was heard
    ai_reply: str                             # AI response
    audio_url: Optional[str] = None           # TTS audio