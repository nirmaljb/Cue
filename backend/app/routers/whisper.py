"""Whisper (Audio Cue) router for calm reassurance after face recognition."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import base64

from app.services.graph_db import graph_db
from app.services.llm import llm_service
from app.services.elevenlabs import generate_speech


router = APIRouter(tags=["whisper"])


class WhisperResponse(BaseModel):
    """Response model for whisper endpoint."""
    audio_url: Optional[str] = None
    text: Optional[str] = None
    reason: Optional[str] = None


@router.get("/whisper/{person_id}", response_model=WhisperResponse)
async def get_whisper(person_id: str):
    """Generate a calm whisper audio cue for a recognized person.
    
    This endpoint:
    1. Fetches person data from Neo4j
    2. Optionally fetches their latest memory
    3. Generates whisper text via LLM
    4. Converts text to speech via ElevenLabs
    5. Returns base64-encoded audio
    
    On any failure, returns null audio (silent fail).
    """
    # 1. Fetch person data
    person = graph_db.get_person(person_id)
    if not person:
        print(f"⚠️ Whisper: person not found: {person_id}")
        return WhisperResponse(reason="person_not_found")
    
    name = person.get("name", "Someone")
    relation = person.get("relation", "someone you know")
    contextual_note = person.get("contextual_note")
    
    # 2. Fetch recent memory (optional)
    recent_memory = None
    try:
        memories = graph_db.get_memories(person_id, limit=1)
        if memories:
            recent_memory = memories[0].get("summary")
    except Exception as e:
        print(f"⚠️ Whisper: failed to fetch memories: {e}")
    
    # 3. Generate whisper text via LLM
    whisper_text = llm_service.generate_whisper_text(
        name=name,
        relation=relation,
        contextual_note=contextual_note,
        recent_memory=recent_memory,
    )
    
    if not whisper_text:
        return WhisperResponse(reason="generation_failed")
    
    # 4. Generate audio via ElevenLabs
    audio_bytes = await generate_speech(whisper_text)
    
    if not audio_bytes:
        return WhisperResponse(text=whisper_text, reason="tts_failed")
    
    # 5. Return base64-encoded audio
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_url = f"data:audio/mpeg;base64,{audio_base64}"
    
    return WhisperResponse(
        audio_url=audio_url,
        text=whisper_text,
    )
