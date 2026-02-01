"""Face recognition API router."""

from fastapi import APIRouter, HTTPException
import os

from app.models.schemas import (
    RecognizeFaceRequest,
    RecognizeFaceResponse,
    PersonStatus,
)
from app.services.face_recognition import face_recognition
from app.services.vector_db import vector_db
from app.services.graph_db import graph_db
from app.utils.image import decode_base64_image

# Directory to store face thumbnails
FACE_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "face_images")
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)


router = APIRouter(tags=["Face Recognition"])


def save_face_thumbnail(person_id: str, image_base64: str):
    """Save a face thumbnail for a person."""
    try:
        image = decode_base64_image(image_base64)
        image.thumbnail((200, 200))
        image_path = os.path.join(FACE_IMAGES_DIR, f"{person_id}.jpg")
        image.save(image_path, "JPEG", quality=85)
        return True
    except Exception as e:
        print(f"Failed to save face thumbnail: {e}")
        return False


@router.post("/recognize-face", response_model=RecognizeFaceResponse)
async def recognize_face(request: RecognizeFaceRequest):
    """Recognize a face from multiple images.
    
    Multi-frame recognition flow:
    1. Try each frame to extract face embedding
    2. Search Qdrant for each embedding
    3. Return the best matching CONFIRMED person
    4. If no match in any frame, return not recognized
    """
    if not request.images_base64:
        raise HTTPException(
            status_code=400,
            detail="No images provided",
        )
    
    print(f"🔍 Processing {len(request.images_base64)} frames for recognition...")
    
    best_match = None
    best_confidence = 0.0
    best_person = None
    
    # Try each frame
    for i, image_base64 in enumerate(request.images_base64):
        try:
            # Extract face embedding
            embedding = face_recognition.extract_embedding(image_base64)
            
            if embedding is None:
                print(f"  Frame {i+1}: No face detected")
                continue
            
            # Search for matching face
            matches = vector_db.search_face(embedding)
            
            if matches:
                match = matches[0]
                print(f"  Frame {i+1}: Found match - person_id: {match['person_id'][:8]}..., status: {match['status']}, confidence: {match['confidence']:.3f}")
                
                # Only consider CONFIRMED persons
                if match["status"] == "confirmed":
                    if match["confidence"] > best_confidence:
                        person = graph_db.get_person(match["person_id"])
                        if person:
                            best_match = match
                            best_confidence = match["confidence"]
                            best_person = person
                            print(f"    → Best match updated: {person.get('name', 'Unknown')}")
                else:
                    print(f"    → Skipped: status is '{match['status']}', not 'confirmed'")
            else:
                print(f"  Frame {i+1}: No match found")
                
        except Exception as e:
            print(f"  Frame {i+1}: Error - {e}")
            continue
    
    # Return best match if found
    if best_match and best_person:
        # Update last seen timestamp
        graph_db.update_last_seen(best_match["person_id"])
        
        print(f"✅ Best match: {best_person.get('name', 'Unknown')} (confidence: {best_confidence:.3f})")
        return RecognizeFaceResponse(
            recognized=True,
            status=PersonStatus.CONFIRMED,
            person_id=best_match["person_id"],
            confidence=best_confidence,
            message=f"Recognized {best_person.get('name', 'Unknown')}",
        )
    
    # No match found in any frame
    print(f"❓ No match found in any of the {len(request.images_base64)} frames")
    return RecognizeFaceResponse(
        recognized=False,
        status=PersonStatus.TEMPORARY,
        person_id="",
        message="Face not enrolled. Please enroll this person via the Caregiver Panel.",
    )
