import os
import uuid
import io
from gtts import gTTS

OUTPUT_DIR = "generated_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def speech_to_text(audio_bytes: bytes, audio_format: str = "wav") -> str:
    """
    Convert audio to text using faster-whisper.
    Runs completely locally — no API key needed.

    faster-whisper downloads the model on first use (~40MB).
    Subsequent uses are instant.
    """
    try:
        from faster_whisper import WhisperModel

        # tiny model = fast, good enough for clear speech
        # Downloads automatically on first run
        model = WhisperModel("tiny", device="cpu", compute_type="int8")

        # Save audio bytes to temp file
        temp_path = os.path.join(OUTPUT_DIR, f"temp_audio_{uuid.uuid4()}.{audio_format}")

        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        # Transcribe
        segments, info = model.transcribe(temp_path, beam_size=5)
        transcript = " ".join([seg.text for seg in segments]).strip()

        # Clean up temp file
        os.remove(temp_path)

        print(f"🎤 Transcribed: {transcript[:80]}")
        return transcript

    except Exception as e:
        print(f"STT error: {e}")
        return ""


def text_to_speech(text: str, language: str = "en") -> str:
    """
    Convert text to speech using gTTS (Google Text-to-Speech).
    Returns path to the generated MP3 file.

    gTTS needs internet connection.
    Supports multiple languages (en, hi, te, ta etc.)
    """
    try:
        file_name = f"tts_{uuid.uuid4()}.mp3"
        file_path = os.path.join(OUTPUT_DIR, file_name)

        tts = gTTS(text=text[:500], lang=language, slow=False)
        tts.save(file_path)

        print(f"🔊 TTS saved: {file_name}")
        return file_name

    except Exception as e:
        print(f"TTS error: {e}")
        return None