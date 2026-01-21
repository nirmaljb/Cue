"""HUD context API router."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    HUDContextRequest,
    HUDContextResponse,
    PersonStatus,
)
from app.services.graph_db import graph_db
from app.services.vector_db import vector_db
from app.services.llm import llm_service


router = APIRouter(tags=["HUD"])


@router.post("/hud-context", response_model=HUDContextResponse)
async def get_hud_context(request: HUDContextRequest):
    """Generate HUD context for a person.
    
    Flow:
    - CONFIRMED: Fetch profile with static contextual note.
    - TEMPORARY/UNKNOWN: Return minimal response (clean state).
    """
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
    
    
    # Dementia-Safe: Return static contextual note
    # No AI emotional analysis
    
    # Fetch routines
    routines = graph_db.get_routines(request.person_id)
    selected_routine = None
    display_contextual_note = None
    
    if routines:
        # Get recent memory for context
        memories = graph_db.get_memories(request.person_id, limit=1)
        recent_memory = memories[0].get("summary") if memories else None
        
        # LLM selects best routine
        selected_routine = llm_service.select_best_routine(routines, recent_memory)
        
        # Condense to keep HUD clean
        if selected_routine:
            selected_routine = llm_service.condense_to_few_words(selected_routine)
            print(f"✅ Condensed routine: {selected_routine}")
            # Don't show contextual note when we have a routine
            display_contextual_note = None
        else:
            # Failed to select routine, fall back to contextual note
            contextual_note = person.get("contextual_note", "")
            if contextual_note and contextual_note.strip():
                display_contextual_note = llm_service.condense_to_few_words(contextual_note)
                print(f"✅ Using contextual note (no routine selected): {display_contextual_note}")
    else:
        # No routines yet - use contextual note as fallback
        contextual_note = person.get("contextual_note", "")
        if contextual_note and contextual_note.strip():
            # Transform and condense contextual note
            routine_style = llm_service.transform_contextual_note_to_routine(contextual_note)
            selected_routine = llm_service.condense_to_few_words(routine_style)
            print(f"✅ Using contextual note fallback as routine: {selected_routine}")
        else:
            print(f"ℹ️ No routines or contextual note for person {request.person_id}")
    
    return HUDContextResponse(
        name=person.get("name"),
        relation=person.get("relation"),
        contextual_note=display_contextual_note,  # Only set if no routine available
        routine=selected_routine,
        speak=False,
        speechText=None,
    )
