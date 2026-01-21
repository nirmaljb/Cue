"""Routine extraction and analysis service."""

from app.services.graph_db import graph_db
from app.services.llm import llm_service


async def analyze_and_update_routines(person_id: str):
    """Analyze memories and update routines for a person.
    
    Triggered after every 2 new memories.
    
    Args:
        person_id: Person ID to analyze
    """
    print(f"🔍 Analyzing routines for person {person_id}...")
    
    # Check memory count
    memory_count = graph_db.get_memory_count(person_id)
    print(f"📊 Memory count: {memory_count}")
    
    # Get person for fallback
    person = graph_db.get_person(person_id)
    if not person:
        print(f"⚠️ Person {person_id} not found")
        return
    
    # If no memories, create routine from contextual note
    if memory_count == 0:
        contextual_note = person.get("contextual_note", "")
        if contextual_note:
            print(f"💡 No memories yet, transforming contextual note")
            routine_text = llm_service.transform_contextual_note_to_routine(contextual_note)
            
            # Delete old routines
            graph_db.delete_all_routines(person_id)
            
            # Create new routine
            graph_db.create_routine(
                person_id=person_id,
                text=routine_text,
                confidence=0.6,  # Lower confidence for contextual note
                source="contextual_note"
            )
            print(f"✅ Created routine from contextual note: {routine_text}")
        return
    
    # Get all memories
    memories = graph_db.get_memories(person_id, limit=50)
    
    # Extract routines using LLM
    extracted_routines = llm_service.extract_routines_from_memories(memories)
    
    if not extracted_routines:
        print(f"📭 No routines extracted from {len(memories)} memories")
        # Keep using contextual note as fallback if no routines found
        contextual_note = person.get("contextual_note", "")
        if contextual_note:
            routine_text = llm_service.transform_contextual_note_to_routine(contextual_note)
            graph_db.delete_all_routines(person_id)
            graph_db.create_routine(
                person_id=person_id,
                text=routine_text,
                confidence=0.5,
                source="contextual_note"
            )
            print(f"✅ Using contextual note fallback: {routine_text}")
        return
    
    print(f"📝 Extracted {len(extracted_routines)} routines")
    
    # Delete existing routines
    graph_db.delete_all_routines(person_id)
    
    # Create new routines
    for routine in extracted_routines:
        routine_id = graph_db.create_routine(
            person_id=person_id,
            text=routine.get("text", ""),
            confidence=routine.get("confidence", 0.5),
            source="memories"
        )
        print(f"✅ Created routine {routine_id}: {routine.get('text')}")
    
    print(f"🎯 Routine analysis complete for person {person_id}")
