"""Neo4j graph database service for people, relationships, and memories."""

from neo4j import GraphDatabase
from neo4j.exceptions import SessionExpired, ServiceUnavailable
from typing import Optional
from datetime import datetime
import uuid
from functools import wraps

from app.config import settings


def retry_on_connection_error(max_retries=3):
    """Decorator to retry Neo4j operations on connection errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    # Ensure connection before operation
                    if not self._connected or not self.driver:
                        print(f"🔄 Reconnecting to Neo4j (attempt {attempt + 1})...")
                        self.reconnect()
                    return func(self, *args, **kwargs)
                except (SessionExpired, ServiceUnavailable) as e:
                    last_error = e
                    print(f"⚠️ Neo4j connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    self._connected = False
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator


class GraphDBService:
    """Service for interacting with Neo4j graph database."""
    
    def __init__(self):
        self.driver = None
        self._connected = False
    
    def connect(self):
        """Connect to Neo4j cloud instance."""
        if self._connected and self.driver:
            return
        
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
            )
            self._ensure_constraints()
            self._connected = True
            print("✅ Connected to Neo4j")
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            self._connected = False
            raise
    
    def reconnect(self):
        """Force reconnection to Neo4j."""
        self.close()
        self.connect()
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            try:
                self.driver.close()
            except:
                pass
            self.driver = None
            self._connected = False
    
    def _ensure_constraints(self):
        """Create unique constraints if they don't exist."""
        with self.driver.session() as session:
            # Unique constraint on Person id
            session.run("""
                CREATE CONSTRAINT person_id IF NOT EXISTS
                FOR (p:Person) REQUIRE p.id IS UNIQUE
            """)
            # Unique constraint on Memory id
            session.run("""
                CREATE CONSTRAINT memory_id IF NOT EXISTS
                FOR (m:Memory) REQUIRE m.id IS UNIQUE
            """)
            # Unique constraint on Routine id
            session.run("""
                CREATE CONSTRAINT routine_id IF NOT EXISTS
                FOR (r:Routine) REQUIRE r.id IS UNIQUE
            """)
    
    def health_check(self) -> bool:
        """Check if Neo4j is connected and healthy."""
        try:
            if not self._connected:
                self.connect()
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False
    
    # ============================================
    # Person Operations
    # ============================================
    
    def create_person(
        self,
        status: str = "temporary",
        name: str = None,
        relation: str = None,
        contextual_note: str = None,
    ) -> str:
        """Create a new person node."""
        person_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with self.driver.session() as session:
            session.run("""
                CREATE (p:Person {
                    id: $id,
                    status: $status,
                    name: $name,
                    relation: $relation,
                    contextual_note: $contextual_note,
                    created_at: $created_at,
                    confirmed_at: null,
                    last_seen_at: $created_at
                })
            """, id=person_id, status=status, name=name, 
                relation=relation, contextual_note=contextual_note, created_at=now)
        
        return person_id
    
    @retry_on_connection_error(max_retries=3)
    def get_person(self, person_id: str) -> Optional[dict]:
        """Get a person by ID."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {id: $id})
                RETURN p
            """, id=person_id)
            record = result.single()
            if record:
                return dict(record["p"])
        return None
    
    @retry_on_connection_error(max_retries=3)
    def update_person(
        self,
        person_id: str,
        name: str = None,
        relation: str = None,
        status: str = None,
        contextual_note: str = None,
    ):
        """Update a person's details."""
        now = datetime.utcnow().isoformat()
        
        with self.driver.session() as session:
            if name is not None:
                session.run("""
                    MATCH (p:Person {id: $id})
                    SET p.name = $name
                """, id=person_id, name=name)
            
            if relation is not None:
                session.run("""
                    MATCH (p:Person {id: $id})
                    SET p.relation = $relation
                """, id=person_id, relation=relation)

            if contextual_note is not None:
                session.run("""
                    MATCH (p:Person {id: $id})
                    SET p.contextual_note = $note
                """, id=person_id, note=contextual_note)
            
            if status is not None:
                session.run("""
                    MATCH (p:Person {id: $id})
                    SET p.status = $status,
                        p.confirmed_at = CASE WHEN $status = 'confirmed' THEN $now ELSE p.confirmed_at END
                """, id=person_id, status=status, now=now)
    
    def update_last_seen(self, person_id: str):
        """Update the last seen timestamp for a person."""
        now = datetime.utcnow().isoformat()
        
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Person {id: $id})
                SET p.last_seen_at = $now
            """, id=person_id, now=now)
    
    def update_familiarity(self, person_id: str, increment: float = 0.05):
        """Increment familiarity score (capped at 1.0)."""
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Person {id: $id})
                SET p.familiarity_score = 
                    CASE WHEN p.familiarity_score + $inc > 1.0 
                         THEN 1.0 
                         ELSE p.familiarity_score + $inc 
                    END
            """, id=person_id, inc=increment)
    
    def get_pending_people(self) -> list[dict]:
        """Get all temporary (pending) people."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {status: 'temporary'})
                OPTIONAL MATCH (p)-[:HAS_MEMORY]->(m:Memory)
                WITH p, m
                ORDER BY m.created_at DESC
                WITH p, collect(m)[0] as latest_memory, count(m) as memory_count
                RETURN p, latest_memory, memory_count
            """)
            
            people = []
            for record in result:
                person = dict(record["p"])
                person["interaction_count"] = record["memory_count"]
                if record["latest_memory"]:
                    person["last_memory_summary"] = record["latest_memory"]["summary"]
                else:
                    person["last_memory_summary"] = None
                people.append(person)
            
            return people
    
    def get_confirmed_people(self) -> list[dict]:
        """Get all confirmed people."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {status: 'confirmed'})
                RETURN p
                ORDER BY p.name
            """)
            
            return [dict(record["p"]) for record in result]
    
    def delete_person(self, person_id: str):
        """Delete a person and all their memories."""
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Person {id: $id})
                OPTIONAL MATCH (p)-[:HAS_MEMORY]->(m:Memory)
                DETACH DELETE p, m
            """, id=person_id)
    
    # ============================================
    # Memory Operations
    # ============================================
    
    def create_memory(
        self,
        person_id: str,
        summary: str,
        emotional_tone: str,
        important_event: str = None,
        raw_transcript: str = None,
    ) -> str:
        """Create a memory and link it to a person."""
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Person {id: $person_id})
                CREATE (m:Memory {
                    id: $memory_id,
                    summary: $summary,
                    emotional_tone: $emotional_tone,
                    important_event: $important_event,
                    raw_transcript: $raw_transcript,
                    created_at: $created_at
                })
                CREATE (p)-[:HAS_MEMORY]->(m)
            """, person_id=person_id, memory_id=memory_id, summary=summary,
                emotional_tone=emotional_tone, important_event=important_event,
                raw_transcript=raw_transcript, created_at=now)
        
        return memory_id
    
    def get_memories(self, person_id: str, limit: int = 10) -> list[dict]:
        """Get memories for a person, ordered by recency."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {id: $id})-[:HAS_MEMORY]->(m:Memory)
                RETURN m
                ORDER BY m.created_at DESC
                LIMIT $limit
            """, id=person_id, limit=limit)
            
            return [dict(record["m"]) for record in result]
    
    def delete_memory(self, memory_id: str):
        """Delete a specific memory."""
        with self.driver.session() as session:
            session.run("""
                MATCH (m:Memory {id: $id})
                DETACH DELETE m
            """, id=memory_id)
    
    # ============================================
    # Routines
    # ============================================
    
    @retry_on_connection_error()
    def create_routine(
        self,
        person_id: str,
        text: str,
        confidence: float,
        source: str = "memories"
    ) -> str:
        """Create a routine and link to person.
        
        Args:
            person_id: Person ID
            text: Routine text (e.g., "You usually have tea together.")
            confidence: Confidence score 0.0-1.0
            source: "memories" or "contextual_note"
        
        Returns:
            routine_id: Created routine ID
        """
        routine_id = str(uuid.uuid4())
        
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Person {id: $person_id})
                CREATE (r:Routine {
                    id: $routine_id,
                    person_id: $person_id,
                    text: $text,
                    confidence: $confidence,
                    source: $source,
                    created_at: datetime(),
                    last_updated: datetime()
                })
                CREATE (p)-[:HAS_ROUTINE]->(r)
            """, person_id=person_id, routine_id=routine_id, text=text,
                confidence=confidence, source=source)
        
        return routine_id
    
    @retry_on_connection_error()
    def get_routines(self, person_id: str) -> list[dict]:
        """Get all routines for a person.
        
        Returns:
            List of routine dicts with id, text, confidence, source
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {id: $person_id})-[:HAS_ROUTINE]->(r:Routine)
                RETURN r.id as id, r.text as text, r.confidence as confidence,
                       r.source as source, r.created_at as created_at
                ORDER BY r.confidence DESC, r.created_at DESC
            """, person_id=person_id)
            
            routines = []
            for record in result:
                routines.append({
                    "id": record["id"],
                    "text": record["text"],
                    "confidence": record["confidence"],
                    "source": record["source"],
                    "created_at": record["created_at"]
                })
            
            return routines
    
    @retry_on_connection_error()
    def delete_all_routines(self, person_id: str):
        """Delete all routines for a person (before re-analysis)."""
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Person {id: $person_id})-[:HAS_ROUTINE]->(r:Routine)
                DETACH DELETE r
            """, person_id=person_id)
    
    @retry_on_connection_error()
    def get_memory_count(self, person_id: str) -> int:
        """Get total number of memories for a person."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {id: $person_id})-[:HAS_MEMORY]->(m:Memory)
                RETURN count(m) as count
            """, person_id=person_id)
            
            record = result.single()
            return record["count"] if record else 0
    
    # ============================================
    # Worker Support Methods
    # ============================================
    
    @retry_on_connection_error()
    def update_person_timestamp(self, person_id: str, field: str):
        """Update a timestamp field on person node."""
        with self.driver.session() as session:
            session.run(f"""
                MATCH (p:Person {{id: $person_id}})
                SET p.{field} = datetime()
            """, person_id=person_id)
    
    @retry_on_connection_error()
    def get_people_needing_routine_analysis(self) -> list[dict]:
        """Find people who need routine extraction.
        
        Criteria:
        - Has memories (count > 0)
        - Memory count is even (divisible by 2)
        - Never analyzed OR last analysis before last memory save
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[:HAS_MEMORY]->(m:Memory)
                WITH p, count(m) as memory_count
                WHERE memory_count % 2 = 0 
                  AND (p.last_routine_analysis IS NULL 
                       OR p.last_routine_analysis < p.last_memory_saved)
                RETURN p.id as person_id, p.name as name, memory_count
                LIMIT 10
            """)
            return [dict(record) for record in result]
    
    @retry_on_connection_error()
    def mark_routine_analysis_complete(self, person_id: str):
        """Mark that routine analysis was completed."""
        self.update_person_timestamp(person_id, "last_routine_analysis")


# Singleton instance
graph_db = GraphDBService()
