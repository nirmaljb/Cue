"""HUD context API router with multi-language support."""

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    HUDContextRequest,
    HUDContextResponse,
    PersonStatus,
)
from app.services.graph_db import graph_db
from app.services.vector_db import vector_db
from app.services.llm import llm_service
from app.services.sarvam import sarvam_service
from app.data.relations import get_relation, SUPPORTED_LANGUAGES


router = APIRouter(tags=["HUD"])


@router.post("/hud-context", response_model=HUDContextResponse)
async def get_hud_context(
    request: HUDContextRequest,
    lang: str = Query(default="en", description="Language code: en, hi, ta, bn, te")
):
    """Generate HUD context for a person with multi-language support.
    
    Flow:
    - CONFIRMED: Fetch profile, translate content to target language.
    - TEMPORARY/UNKNOWN: Return minimal response (clean state).
    
    Args:
        request: HUD context request with person_id and status
        lang: Target language code (en, hi, ta, bn, te)
    """
    # Validate language
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    
    if request.status == PersonStatus.TEMPORARY:
        # Clean state for temporary persons (Dementia-Safe: Silence)
        return HUDContextResponse(
            name=None,
            relation=None,
            contextual_note=None,
            speak=False,
            speechText=None,
        )
    
    # CONFIRMED person - fetch profile
    person = graph_db.get_person(request.person_id)
    
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )
    
    # Get person data
    name = person.get("name", "")
    relation_en = person.get("relation", "")
    
    # Translate relation using static dictionary
    relation_translated = get_relation(relation_en, lang)
    print(f"🌐 Relation: {relation_en} → {relation_translated} ({lang})")
    
    # HUD Display Priority: Contextual Note > Routines
    display_text = None
    contextual_note = person.get("contextual_note", "")
    
    if contextual_note and contextual_note.strip():
        # Priority 1: Use contextual note (condense via LLM)
        condensed = llm_service.condense_to_few_words(contextual_note)
        
        # Translate if not English
        if lang != "en" and condensed:
            translated = await sarvam_service.translate(condensed, "en", lang)
            display_text = translated or condensed
        else:
            display_text = condensed
        
        print(f"✅ HUD using contextual note: {display_text}")
    else:
        # Priority 2: Fall back to routines (if no contextual note)
        routines = graph_db.get_routines(request.person_id)
        
        if routines:
            # Get recent memory for context
            memories = graph_db.get_memories(request.person_id, limit=1)
            recent_memory = memories[0].get("summary") if memories else None
            
            # LLM selects best routine (in English)
            selected_routine = llm_service.select_best_routine(routines, recent_memory)
            
            if selected_routine:
                selected_routine = llm_service.condense_to_few_words(selected_routine)
                
                # Translate if not English
                if lang != "en" and selected_routine:
                    translated = await sarvam_service.translate(selected_routine, "en", lang)
                    display_text = translated or selected_routine
                else:
                    display_text = selected_routine
                
                print(f"✅ HUD using routine (fallback): {display_text}")
        else:
            print(f"ℹ️ No contextual note or routines for person {request.person_id}")
    
    return HUDContextResponse(
        name=name,  # Keep name as-is (no translation/transliteration)
        relation=relation_translated,
        contextual_note=None,  # Not used anymore
        routine=display_text,  # Contextual note (priority) or routine (fallback)
        speak=False,
        speechText=None,  # Whisper handled by separate endpoint
    )
