"""ElevenLabs Text-to-Speech service for Whisper feature (V3)."""

import httpx
from typing import Optional

from app.config import settings


# Jessica voice ID (Playful, Bright, Warm)
JESSICA_VOICE_ID = "cgSgspJ2msm6clMCkdW9"


async def generate_speech(text: str) -> Optional[bytes]:
    """Generate speech audio using ElevenLabs V3 Conversational AI.
    
    Uses Jessica voice with enhance features for natural spacing and emotion.
    Configured for slow, whisper-like delivery with increased spacing.
    
    Args:
        text: Text to convert to speech (1-2 sentences)
    
    Returns:
        MP3 audio bytes, or None if failed
    """
    if not settings.ELEVENLABS_API_KEY:
        print("⚠️ ELEVENLABS_API_KEY not configured")
        return None
    
    # Add spacing between sentences for slower, more deliberate delivery
    # Replace periods with periods + pause markers
    spaced_text = text.replace('. ', '... ')  # Triple dots = longer pause
    if not spaced_text.endswith('...'):
        spaced_text = spaced_text.replace('.', '...')
    
    # Prepend whisper instruction for ElevenLabs to interpret
    whisper_prompt = f"[whisper, slow, gentle] {spaced_text}"
    
    try:
        async with httpx.AsyncClient() as client:
            # V3 Conversational AI endpoint with text enhancement
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{JESSICA_VOICE_ID}/with-timestamps",
                headers={
                    "xi-api-key": settings.ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": whisper_prompt,
                    "model_id": "eleven_turbo_v2_5",  # V3 model
                    "voice_settings": {
                        "stability": 0.85,          # Very high for calm, whispered delivery
                        "similarity_boost": 0.7,    # Higher for voice consistency  
                        "style": 0.05,              # Minimal style for whisper effect
                        "use_speaker_boost": False, # Disable for softer, intimate sound
                    },
                    # V3 enhancement features
                    "pronunciation_dictionary_locators": [],
                    "seed": None,
                    "previous_text": None,
                    "next_text": None,
                    "previous_request_ids": [],
                    "next_request_ids": [],
                },
                timeout=20.0,
            )
            
            if response.status_code == 200:
                # V3 returns JSON with audio_base64
                response_data = response.json()
                audio_base64 = response_data.get("audio_base64")
                
                if audio_base64:
                    import base64
                    audio_bytes = base64.b64decode(audio_base64)
                    print(f"✅ ElevenLabs V3 (Jessica) whisper generated ({len(audio_bytes)} bytes)")
                    return audio_bytes
                else:
                    print("⚠️ No audio in V3 response")
                    return None
            else:
                print(f"⚠️ ElevenLabs V3 failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"⚠️ ElevenLabs V3 error: {e}")
        return None
