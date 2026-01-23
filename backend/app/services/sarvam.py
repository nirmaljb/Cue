"""Sarvam AI service for Indian language translation and TTS.

API Documentation: https://docs.sarvam.ai
- Translation: /translate endpoint (mayura:v1 model)
- TTS: /text-to-speech endpoint (bulbul:v2 model, Vidya voice)
"""

import httpx
import os
import base64
from typing import Optional

# Sarvam API configuration
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_BASE_URL = "https://api.sarvam.ai"

# Language code mapping (our codes -> Sarvam BCP-47 codes)
LANGUAGE_CODES = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "bn": "bn-IN",
    "te": "te-IN",
}

# TTS configuration
TTS_VOICE = "vidya"  # Female voice - smooth and comforting
TTS_PACE = 0.9  # Slightly slower for clarity
TTS_MODEL = "bulbul:v2"

# Translation configuration
TRANSLATE_MODEL = "mayura:v1"


class SarvamService:
    """Sarvam AI API client for translation and TTS."""
    
    def __init__(self):
        self.api_key = SARVAM_API_KEY
        self._client = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-load async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=SARVAM_BASE_URL,
                headers={
                    "api-subscription-key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client
    
    async def translate(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi"
    ) -> Optional[str]:
        """Translate text from source to target language.
        
        Args:
            text: Text to translate (max 1000 chars for mayura:v1)
            source_lang: Source language code (en, hi, ta, bn, te)
            target_lang: Target language code
        
        Returns:
            Translated text or None if failed
        """
        if not self.api_key:
            print("⚠️ Sarvam API key not configured")
            return None
        
        # Same language - no translation needed
        if source_lang == target_lang:
            return text
        
        # Get BCP-47 codes
        source_code = LANGUAGE_CODES.get(source_lang, "en-IN")
        target_code = LANGUAGE_CODES.get(target_lang, "hi-IN")
        
        try:
            response = await self.client.post(
                "/translate",
                json={
                    "input": text[:1000],  # Max 1000 chars
                    "source_language_code": source_code,
                    "target_language_code": target_code,
                    "model": TRANSLATE_MODEL,
                    "mode": "formal",  # Respectful language
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                translated = data.get("translated_text", "")
                print(f"🌐 Translated ({source_lang}→{target_lang}): {text[:30]}... → {translated[:30]}...")
                return translated
            else:
                print(f"⚠️ Sarvam translate error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"⚠️ Sarvam translate error: {e}")
            return None
    
    async def text_to_speech(
        self,
        text: str,
        lang: str = "hi"
    ) -> Optional[bytes]:
        """Convert text to speech audio.
        
        Args:
            text: Text to speak (max 1500 chars)
            lang: Language code (hi, ta, bn, te)
        
        Returns:
            Audio bytes (WAV format) or None if failed
        """
        if not self.api_key:
            print("⚠️ Sarvam API key not configured")
            return None
        
        # Get BCP-47 code
        lang_code = LANGUAGE_CODES.get(lang, "hi-IN")
        
        try:
            response = await self.client.post(
                "/text-to-speech",
                json={
                    "inputs": [text[:1500]],  # Max 1500 chars
                    "target_language_code": lang_code,
                    "speaker": TTS_VOICE,
                    "pace": TTS_PACE,
                    "model": TTS_MODEL,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                # Response contains base64-encoded audio
                audios = data.get("audios", [])
                if audios:
                    audio_base64 = audios[0]
                    audio_bytes = base64.b64decode(audio_base64)
                    print(f"🔊 Sarvam TTS generated: {len(audio_bytes)} bytes ({lang})")
                    return audio_bytes
                else:
                    print("⚠️ Sarvam TTS: no audio in response")
                    return None
            else:
                print(f"⚠️ Sarvam TTS error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"⚠️ Sarvam TTS error: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
sarvam_service = SarvamService()


# Helper function for sync translate (using LLM fallback if Sarvam unavailable)
def translate_sync_fallback(text: str, target_lang: str) -> str:
    """Synchronous translation with fallback to original text.
    
    For use in sync contexts where async isn't available.
    Returns original text if translation fails.
    """
    # This is a sync fallback - returns original if can't translate
    # Actual translation should use async translate() method
    return text
