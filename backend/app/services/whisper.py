"""Whisper speech-to-text service using Groq."""

from groq import Groq
import base64
import tempfile
import os
from typing import Optional

from app.config import settings


class WhisperService:
    """Service for speech-to-text using Groq's Whisper API."""
    
    def __init__(self):
        self.client: Optional[Groq] = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the Groq client."""
        if self._initialized:
            return
        
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self._initialized = True
        print("✅ Groq Whisper client initialized")
    
    def transcribe(self, audio_base64: str) -> str:
        """Transcribe audio to text.
        
        Args:
            audio_base64: Base64 encoded audio (with or without data URI prefix)
        
        Returns:
            Transcribed text
        """
        if not self._initialized:
            self.initialize()
        
        # Remove data URI prefix if present
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",")[1]
        
        # Decode base64 to bytes
        audio_bytes = base64.b64decode(audio_base64)
        
        # Write to temporary file (Groq API requires file)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            # Transcribe using Groq Whisper
            with open(temp_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=(temp_path, audio_file.read()),
                    model="whisper-large-v3",
                    response_format="text",
                )
            
            return transcription.strip()
            
        except Exception as e:
            print(f"⚠️ Whisper error: {e}")
            return ""
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# Singleton instance
whisper_service = WhisperService()
