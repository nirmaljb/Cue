"""Whisper (Audio Cue) router with multi-language support.

Uses fixed templates per language with Sarvam TTS for Indian languages
and ElevenLabs for English.
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
import base64

from app.services.graph_db import graph_db
from app.services.llm import llm_service
from app.services.elevenlabs import generate_speech
from app.services.sarvam import sarvam_service
from app.data.relations import get_relation, SUPPORTED_LANGUAGES
from app.data.whisper_templates import format_whisper


router = APIRouter(tags=["whisper"])


class WhisperResponse(BaseModel):
    """Response model for whisper endpoint."""
    audio_url: Optional[str] = None
    text: Optional[str] = None
    reason: Optional[str] = None
    lang: Optional[str] = None


@router.get("/whisper/{person_id}", response_model=WhisperResponse)
async def get_whisper(
    person_id: str,
    lang: str = Query(default="en", description="Language code: en, hi, ta, bn, te")
):
    """Generate a multi-language audio cue for a recognized person.
    
    This endpoint:
    1. Fetches person data from Neo4j
    2. Fetches routines for context
    3. Translates content to target language
    4. Uses fixed templates with placeholders
    5. Generates audio via Sarvam (Indic) or ElevenLabs (English)
    
    On any failure, returns text without audio (silent fail).
    """
    # Validate language
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    
    # 1. Fetch person data
    person = graph_db.get_person(person_id)
    if not person:
        print(f"⚠️ Whisper: person not found: {person_id}")
        return WhisperResponse(reason="person_not_found", lang=lang)
    
    name = person.get("name", "Someone")
    relation_en = person.get("relation", "someone you know")
    contextual_note = person.get("contextual_note", "")
    
    # 2. Translate relation using static dictionary
    relation_translated = get_relation(relation_en, lang)
    print(f"🌐 Relation for whisper: {relation_en} → {relation_translated} ({lang})")
    
    # 3. Fetch routines from database
    routines = graph_db.get_routines(person_id)
    
    # 4. Build routine text
    routine_text = None
    if routines and len(routines) > 0:
        # Select best routine
        memories = graph_db.get_memories(person_id, limit=1)
        recent_memory = memories[0].get("summary") if memories else None
        routine_en = llm_service.select_best_routine(routines, recent_memory)
        
        if routine_en:
            routine_en = llm_service.condense_to_few_words(routine_en)
            
            # Translate routine if not English
            if lang != "en":
                translated = await sarvam_service.translate(routine_en, "en", lang)
                routine_text = translated or routine_en
            else:
                routine_text = routine_en
            
            print(f"🌐 Routine for whisper: {routine_en} → {routine_text}")
    
    # 5. Format whisper using template
    whisper_text = format_whisper(
        name=name,
        relation=relation_translated,
        routine=routine_text,
        lang=lang
    )
    
    print(f"🗣️ Whisper text ({lang}): {whisper_text[:100]}...")
    
    if not whisper_text:
        return WhisperResponse(reason="generation_failed", lang=lang)
    
    # 6. Generate audio
    audio_bytes = None
    
    if lang == "en":
        # English: Use ElevenLabs (Jyot voice)
        audio_bytes = await generate_speech(whisper_text)
    else:
        # Indian languages: Use Sarvam TTS (Vidya voice)
        audio_bytes = await sarvam_service.text_to_speech(whisper_text, lang)
    
    if not audio_bytes:
        # Fail silently - return text without audio
        print(f"⚠️ TTS failed for {lang}, returning text only")
        return WhisperResponse(text=whisper_text, reason="tts_failed", lang=lang)
    
    # 7. Return base64-encoded audio
    # Sarvam returns WAV, ElevenLabs returns MP3
    mime_type = "audio/wav" if lang != "en" else "audio/mpeg"
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_url = f"data:{mime_type};base64,{audio_base64}"
    
    return WhisperResponse(
        audio_url=audio_url,
        text=whisper_text,
        lang=lang,
    )
