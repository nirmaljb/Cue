"""ElevenLabs text-to-speech service."""

from typing import Optional
import httpx
from app.config import settings

# Priyanka voice ID (Playful, Bright and Warm)
PRIYANKA_VOICE_ID = "jsCqWAovK2LkecY7zXl4"


async def generate_speech(text: str) -> Optional[bytes]:
    """Generate speech audio using ElevenLabs with Priyanka voice.
    
    Uses default voice settings for natural, clear speech.
    
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
            # Standard TTS endpoint with default settings
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{PRIYANKA_VOICE_ID}",
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_turbo_v2_5",
                    # Default voice settings (omit for ElevenLabs defaults)
                },
                timeout=20.0,
            )
            
            if response.status_code == 200:
                audio_bytes = response.content
                print(f"✅ ElevenLabs (Priyanka) generated ({len(audio_bytes)} bytes)")
                return audio_bytes
            else:
                print(f"⚠️ ElevenLabs failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"⚠️ ElevenLabs error: {e}")
        return None
