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
    - CONFIRMED: Fetch profile + memories, use LLM for emotional cue
    - TEMPORARY: Return neutral fallback (no LLM identity reasoning)
    """
    if request.status == PersonStatus.TEMPORARY:
        # Neutral fallback for temporary persons
        return HUDContextResponse(
            name=None,
            relation=None,
            emotionalCue="Someone you're talking with",
            familiarity=0.0,
            speak=False,
            speechText=None,
        )
    
    # CONFIRMED person - fetch full context
    person = graph_db.get_person(request.person_id)
    
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )
    
    # Fetch memories
    memories = graph_db.get_memories(request.person_id, limit=5)
    
    # Generate HUD context using LLM
    hud_data = llm_service.generate_hud_context(
        name=person.get("name", "Someone"),
        relation=person.get("relation", "Someone you know"),
        memories=memories,
        familiarity_score=person.get("familiarity_score", 0.0),
    )
    
    return HUDContextResponse(
        name=hud_data["name"],
        relation=hud_data["relation"],
        emotionalCue=hud_data["emotionalCue"],
        familiarity=hud_data["familiarity"],
        speak=hud_data["speak"],
        speechText=hud_data.get("speechText"),
    )
