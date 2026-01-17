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
    
    return HUDContextResponse(
        name=person.get("name"),
        relation=person.get("relation"),
        contextual_note=person.get("contextual_note"),
        speak=False,
        speechText=None,
    )
