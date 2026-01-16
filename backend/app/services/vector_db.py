"""Qdrant vector database service for face and memory embeddings."""

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import Optional
import uuid

from app.config import settings


class VectorDBService:
    """Service for interacting with Qdrant vector database."""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self._connected = False
    
    def connect(self):
        """Connect to Qdrant cloud instance."""
        if self._connected:
            return
        
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        self._ensure_collections()
        self._connected = True
    
    def _ensure_collections(self):
        """Create collections if they don't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        # Face embeddings collection (512-dim for FaceNet)
        if settings.FACE_EMBEDDINGS_COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=settings.FACE_EMBEDDINGS_COLLECTION,
                vectors_config=VectorParams(
                    size=512,
                    distance=Distance.COSINE,
                ),
            )
        
        # Memory embeddings collection (384-dim for sentence-transformers)
        if settings.MEMORY_EMBEDDINGS_COLLECTION not in collection_names:
            self.client.create_collection(
                collection_name=settings.MEMORY_EMBEDDINGS_COLLECTION,
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE,
                ),
            )
    
    def health_check(self) -> bool:
        """Check if Qdrant is connected and healthy."""
        try:
            if not self._connected:
                self.connect()
            self.client.get_collections()
            return True
        except Exception:
            return False
    
    # ============================================
    # Face Embeddings
    # ============================================
    
    def store_face_embedding(
        self,
        person_id: str,
        embedding: list[float],
        status: str = "temporary",
    ) -> str:
        """Store a face embedding for a person."""
        point_id = str(uuid.uuid4())
        
        self.client.upsert(
            collection_name=settings.FACE_EMBEDDINGS_COLLECTION,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "person_id": person_id,
                        "status": status,
                    },
                )
            ],
        )
        return point_id
    
    def search_face(
        self,
        embedding: list[float],
        threshold: float = None,
        limit: int = 1,
    ) -> list[dict]:
        """Search for matching faces by embedding."""
        if threshold is None:
            threshold = settings.FACE_SIMILARITY_THRESHOLD
        
        # First, search WITHOUT threshold to see all similarity scores (for debugging)
        all_results = self.client.search(
            collection_name=settings.FACE_EMBEDDINGS_COLLECTION,
            query_vector=embedding,
            limit=5,  # Get top 5 for debugging
        )
        
        # Log all similarity scores for debugging
        if all_results:
            print(f"🔍 Face search results (top 5):")
            for r in all_results:
                print(f"   - person_id: {r.payload['person_id'][:8]}... | status: {r.payload['status']} | similarity: {r.score:.4f}")
        else:
            print(f"🔍 Face search: No embeddings in database")
        
        # Now filter by threshold
        results = [r for r in all_results if r.score >= threshold]
        
        if results:
            print(f"✅ Match found above threshold ({threshold}): {results[0].payload['person_id'][:8]}... with score {results[0].score:.4f}")
        else:
            print(f"❌ No match above threshold ({threshold})")
        
        return [
            {
                "person_id": r.payload["person_id"],
                "status": r.payload["status"],
                "confidence": r.score,
            }
            for r in results[:limit]
        ]
    
    def update_person_status(self, person_id: str, status: str):
        """Update the status of all embeddings for a person."""
        try:
            # First, find all points with this person_id
            scroll_result = self.client.scroll(
                collection_name=settings.FACE_EMBEDDINGS_COLLECTION,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="person_id",
                            match=models.MatchValue(value=person_id),
                        )
                    ]
                ),
                limit=100,
            )
            
            # Get point IDs
            point_ids = [str(point.id) for point in scroll_result[0]]
            
            if point_ids:
                # Update payload for those specific points
                self.client.set_payload(
                    collection_name=settings.FACE_EMBEDDINGS_COLLECTION,
                    payload={"status": status},
                    points=point_ids,
                )
                print(f"✅ Updated {len(point_ids)} embeddings to status: {status}")
        except Exception as e:
            print(f"⚠️ Error updating person status: {e}")
    
    # ============================================
    # Memory Embeddings
    # ============================================
    
    def store_memory_embedding(
        self,
        memory_id: str,
        person_id: str,
        embedding: list[float],
        summary: str,
        emotional_tone: str,
    ) -> str:
        """Store a memory embedding."""
        self.client.upsert(
            collection_name=settings.MEMORY_EMBEDDINGS_COLLECTION,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload={
                        "person_id": person_id,
                        "summary": summary,
                        "emotional_tone": emotional_tone,
                    },
                )
            ],
        )
        return memory_id
    
    def search_memories(
        self,
        person_id: str,
        query_embedding: list[float] = None,
        limit: int = 5,
    ) -> list[dict]:
        """Search memories for a person, optionally by relevance."""
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="person_id",
                    match=models.MatchValue(value=person_id),
                )
            ]
        )
        
        if query_embedding:
            results = self.client.search(
                collection_name=settings.MEMORY_EMBEDDINGS_COLLECTION,
                query_vector=query_embedding,
                query_filter=filter_condition,
                limit=limit,
            )
        else:
            results = self.client.scroll(
                collection_name=settings.MEMORY_EMBEDDINGS_COLLECTION,
                scroll_filter=filter_condition,
                limit=limit,
            )[0]
        
        return [
            {
                "memory_id": str(r.id),
                "summary": r.payload["summary"],
                "emotional_tone": r.payload["emotional_tone"],
            }
            for r in results
        ]
    
    def delete_person_data(self, person_id: str):
        """Delete all embeddings for a person."""
        try:
            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="person_id",
                        match=models.MatchValue(value=person_id),
                    )
                ]
            )
            
            # Delete from face embeddings
            self.client.delete(
                collection_name=settings.FACE_EMBEDDINGS_COLLECTION,
                points_selector=models.FilterSelector(filter=filter_condition),
            )
            
            # Delete from memory embeddings
            self.client.delete(
                collection_name=settings.MEMORY_EMBEDDINGS_COLLECTION,
                points_selector=models.FilterSelector(filter=filter_condition),
            )
            
            print(f"✅ Deleted all embeddings for person: {person_id}")
        except Exception as e:
            print(f"⚠️ Error deleting person data: {e}")


# Singleton instance
vector_db = VectorDBService()
