#!/usr/bin/env python3
"""Manual script to trigger routine extraction for a person."""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.routine import analyze_and_update_routines
from app.services.graph_db import graph_db
from app.services.llm import llm_service
from app.services.vector_db import vector_db

async def main():
    """Extract routines for a specific person."""
    
    # Person ID from your logs
    person_id = "a96a375a-3474-4a6e-b9d9-1dbd2f2247b2"
    
    print("=" * 60)
    print("MANUAL ROUTINE EXTRACTION")
    print("=" * 60)
    
    # Connect to services
    print("\n📡 Connecting to services...")
    graph_db.connect()
    llm_service.initialize()
    vector_db.connect()
    
    # Get person info
    person = graph_db.get_person(person_id)
    if not person:
        print(f"❌ Person {person_id} not found!")
        return
    
    print(f"\n👤 Person: {person.get('name')}")
    print(f"   Relation: {person.get('relation')}")
    print(f"   Contextual Note: {person.get('contextual_note', 'None')}")
    
    # Get memories
    memories = graph_db.get_memories(person_id, limit=50)
    print(f"\n📝 Found {len(memories)} memories")
    
    if memories:
        print("\nMemory summaries:")
        for i, mem in enumerate(memories[:5], 1):
            print(f"   {i}. {mem.get('summary', 'No summary')[:80]}...")
    
    # Trigger routine extraction
    print("\n🔍 Starting routine extraction...")
    print("-" * 60)
    
    await analyze_and_update_routines(person_id)
    
    print("-" * 60)
    
    # Check results
    routines = graph_db.get_routines(person_id)
    print(f"\n✅ Final result: {len(routines)} routines stored")
    
    if routines:
        print("\nExtracted routines:")
        for i, routine in enumerate(routines, 1):
            print(f"   {i}. {routine.get('text')}")
            print(f"      Confidence: {routine.get('confidence')}")
            print(f"      Source: {routine.get('source')}")
    
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
