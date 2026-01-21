"""Memory recording API router."""

from fastapi import APIRouter, HTTPException
from sentence_transformers import SentenceTransformer

from app.models.schemas import (
    MemorySaveRequest,
    MemorySaveResponse,
)
from app.services.graph_db import graph_db
from app.services.vector_db import vector_db
from app.services.whisper import whisper_service
from app.services.llm import llm_service


router = APIRouter(tags=["Memory"])

# Sentence transformer for memory embeddings
_sentence_model = None


def get_sentence_model():
    """Get or initialize the sentence transformer model."""
    global _sentence_model
    if _sentence_model is None:
        print("🔄 Loading sentence transformer model...")
        _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Sentence transformer loaded")
    return _sentence_model


@router.post("/memory/save", response_model=MemorySaveResponse)
async def save_memory(request: MemorySaveRequest):
    """Save a memory from audio recording.
    
    Flow:
    1. Transcribe audio using Whisper
    2. Summarize transcript using LLM
    3. Store memory in Neo4j
    4. Store memory embedding in Qdrant
    5. Update familiarity score
    """
    # Verify person exists
    person = graph_db.get_person(request.person_id)
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )
    
    # Transcribe audio
    transcript = whisper_service.transcribe(request.audio_base64)
    
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail="Could not transcribe audio. Please try again.",
        )
    
    # Summarize transcript using LLM
    memory_data = llm_service.summarize_memory(transcript)
    
    # Store memory in Neo4j
    memory_id = graph_db.create_memory(
        person_id=request.person_id,
        summary=memory_data["summary"],
        emotional_tone=memory_data["emotional_tone"],
        important_event=memory_data.get("important_event"),
        raw_transcript=transcript,
    )
    
    # Generate and store memory embedding
    sentence_model = get_sentence_model()
    embedding = sentence_model.encode(memory_data["summary"]).tolist()
    
    vector_db.store_memory_embedding(
        memory_id=memory_id,
        person_id=request.person_id,
        embedding=embedding,
        summary=memory_data["summary"],
        emotional_tone=memory_data["emotional_tone"],
    )
    
    # Update familiarity score
    graph_db.update_familiarity(request.person_id, increment=0.05)
    graph_db.update_last_seen(request.person_id)
    
    # Update timestamp for background worker to pick up
    graph_db.update_person_timestamp(request.person_id, "last_memory_saved")
    print(f"📝 Memory saved, timestamp updated for background worker")
    
    return MemorySaveResponse(
        status="saved",
        memory_id=memory_id,
        summary=memory_data["summary"],
        emotional_tone=memory_data["emotional_tone"],
    )
