#!/usr/bin/env python3
"""Background worker for routine extraction.

This worker runs as a separate process and polls Neo4j for people
who need routine extraction based on new memories.

Usage:
    Development:
        python -m app.workers.routine_worker
    
    Production:
        nohup python -m app.workers.routine_worker > logs/worker.log 2>&1 &
"""

import asyncio
import time
import signal
import sys
from datetime import datetime

from app.services.graph_db import graph_db
from app.services.llm import llm_service
from app.services.routine import analyze_and_update_routines

# Configuration
POLL_INTERVAL = 30  # seconds between checks
BATCH_SIZE = 5      # max people to process per cycle

# Graceful shutdown
shutdown_flag = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_flag
    print("\n🛑 Shutdown signal received, finishing current work...")
    shutdown_flag = True


async def process_routine_extraction():
    """Main worker loop that polls for work and processes routine extraction."""
    global shutdown_flag
    
    # Startup
    print("=" * 60)
    print("🚀 Routine Extraction Worker Starting")
    print("=" * 60)
    print(f"Poll Interval: {POLL_INTERVAL}s")
    print(f"Batch Size: {BATCH_SIZE} people/cycle")
    print("-" * 60)
    
    # Connect to services
    try:
        graph_db.connect()
        llm_service.initialize()
        print("✅ Services initialized")
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        return
    
    cycle = 0
    
    # Main loop
    while not shutdown_flag:
        cycle += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n[{timestamp}] 🔄 Cycle #{cycle}: Checking for work...")
        
        try:
            # Find people needing routine extraction
            print("   🔍 Querying database for pending work...")
            people = graph_db.get_people_needing_routine_analysis()
            print(f"   ✓ Query complete, found {len(people)} people")
            
            if not people:
                print("   ✓ No pending work")
            else:
                print(f"   📋 Found {len(people)} people needing analysis")
                
                # Process batch (limit to BATCH_SIZE)
                for person in people[:BATCH_SIZE]:
                    person_id = person['person_id']
                    name = person['name']
                    memory_count = person['memory_count']
                    
                    print(f"\n   👤 Processing: {name} ({memory_count} memories)")
                    print(f"      Person ID: {person_id}")
                    
                    try:
                        # Run routine extraction
                        print(f"      🤖 Starting LLM routine extraction...")
                        await analyze_and_update_routines(person_id)
                        
                        # Mark as complete
                        print(f"      ✍️ Marking analysis as complete...")
                        graph_db.mark_routine_analysis_complete(person_id)
                        
                        print(f"   ✅ Completed: {name}")
                        
                    except Exception as e:
                        print(f"   ❌ Failed for {name}: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue with next person even if one fails
        
        except Exception as e:
            print(f"   ⚠️ Error in cycle: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait before next cycle (unless shutting down)
        if not shutdown_flag:
            print(f"\n   💤 Sleeping for {POLL_INTERVAL}s...")
            await asyncio.sleep(POLL_INTERVAL)
    
    # Shutdown
    print("\n" + "=" * 60)
    print("👋 Worker shutdown complete")
    print("=" * 60)
    graph_db.close()


if __name__ == "__main__":
    # Setup graceful shutdown on CTRL+C and termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run worker
    try:
        asyncio.run(process_routine_extraction())
    except KeyboardInterrupt:
        print("\n👋 Worker interrupted")
        sys.exit(0)
