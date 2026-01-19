"""ElevenLabs Text-to-Speech service for Whisper feature."""

import httpx
from typing import Optional

from app.config import settings


async def generate_speech(text: str) -> Optional[bytes]:
    """Generate speech audio using ElevenLabs TTS API.
    
    Args:
        text: Text to convert to speech (1-2 sentences)
    
    Returns:
        MP3 audio bytes, or None if failed
    """
    if not settings.ELEVENLABS_API_KEY:
        print("⚠️ ELEVENLABS_API_KEY not configured")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}",
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.75,       # Calm, consistent
                        "similarity_boost": 0.5, # Natural variation
                        "style": 0.0,            # No dramatic style
                        "use_speaker_boost": False,
                    },
                },
                timeout=15.0,
            )
            
            if response.status_code == 200:
                print(f"✅ ElevenLabs TTS generated ({len(response.content)} bytes)")
                return response.content  # MP3 bytes
            else:
                print(f"⚠️ ElevenLabs TTS failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"⚠️ ElevenLabs TTS error: {e}")
        return None
