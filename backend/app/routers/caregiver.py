"""Caregiver admin API router."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, FileResponse
import os

from app.models.schemas import (
    PendingPeopleResponse,
    PendingPerson,
    ConfirmPersonRequest,
    ConfirmPersonResponse,
)
from app.services.graph_db import graph_db
from app.services.vector_db import vector_db

# Directory where face thumbnails are stored
FACE_IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "face_images")


router = APIRouter(prefix="/caregiver", tags=["Caregiver"])


@router.get("/pending", response_model=PendingPeopleResponse)
async def get_pending_people():
    """Get all temporary (pending) people awaiting caregiver confirmation."""
    pending = graph_db.get_pending_people()
    
    people = [
        PendingPerson(
            person_id=p["id"],
            face_image_url=f"/api/caregiver/face-image/{p['id']}",
            interaction_count=p.get("interaction_count", 0),
            last_memory_summary=p.get("last_memory_summary"),
            last_seen=p.get("last_seen_at", ""),
        )
        for p in pending
    ]
    
    return PendingPeopleResponse(pending_people=people)


@router.post("/confirm", response_model=ConfirmPersonResponse)
async def confirm_person(request: ConfirmPersonRequest):
    """Confirm a temporary person's identity.
    
    This transitions the person from TEMPORARY → CONFIRMED status.
    """
    try:
        # Verify person exists and is temporary
        person = graph_db.get_person(request.person_id)
        
        if not person:
            raise HTTPException(
                status_code=404,
                detail="Person not found",
            )
        
        if person.get("status") == "confirmed":
            raise HTTPException(
                status_code=400,
                detail="Person is already confirmed",
            )
        
        # Update person details in Neo4j
        print(f"📝 Updating person {request.person_id} in Neo4j...")
        graph_db.update_person(
            person_id=request.person_id,
            name=request.name,
            relation=request.relation,
            status="confirmed",
        )
        print(f"✅ Neo4j updated successfully")
        
        # Update status in vector DB
        print(f"📝 Updating person status in Qdrant...")
        vector_db.update_person_status(request.person_id, "confirmed")
        print(f"✅ Qdrant updated successfully")
        
        return ConfirmPersonResponse(
            status="confirmed",
            person_id=request.person_id,
            message=f"Person '{request.name}' is now confirmed as '{request.relation}'",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error confirming person: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm person: {str(e)}",
        )


@router.delete("/person/{person_id}")
async def delete_person(person_id: str):
    """Delete a person and all their associated data."""
    person = graph_db.get_person(person_id)
    
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )
    
    # Delete from both databases
    graph_db.delete_person(person_id)
    vector_db.delete_person_data(person_id)
    
    # Delete face image if exists
    image_path = os.path.join(FACE_IMAGES_DIR, f"{person_id}.jpg")
    if os.path.exists(image_path):
        os.remove(image_path)
    
    return {"status": "deleted", "person_id": person_id}


@router.get("/face-image/{person_id}")
async def get_face_image(person_id: str):
    """Get the face thumbnail for a person.
    
    Returns the actual captured face image if available,
    otherwise returns a placeholder SVG.
    """
    person = graph_db.get_person(person_id)
    
    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )
    
    # Check if actual face image exists
    image_path = os.path.join(FACE_IMAGES_DIR, f"{person_id}.jpg")
    
    if os.path.exists(image_path):
        # Return actual face thumbnail
        return FileResponse(
            image_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "max-age=3600"}
        )
    
    # Fallback: Return placeholder SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <rect width="100" height="100" fill="#374151"/>
        <circle cx="50" cy="40" r="20" fill="#6B7280"/>
        <ellipse cx="50" cy="85" rx="30" ry="20" fill="#6B7280"/>
        <text x="50" y="55" text-anchor="middle" fill="#9CA3AF" font-size="10">
            {person_id[:8]}
        </text>
    </svg>'''
    
    return Response(content=svg, media_type="image/svg+xml")


# Import additional schemas and services for enrollment
from app.models.schemas import (
    EnrollPersonRequest,
    EnrollPersonResponse,
    ConfirmedPerson,
    ConfirmedPeopleResponse,
)
from app.services.face_recognition import face_recognition
from app.utils.image import decode_base64_image


@router.post("/enroll", response_model=EnrollPersonResponse)
async def enroll_person(request: EnrollPersonRequest):
    """Enroll a new person with their photo.
    
    This creates a CONFIRMED person directly (pre-enrollment by caregiver).
    Used for MVP to register known faces before patient mode.
    """
    try:
        print(f"📝 Enrolling new person: {request.name} ({request.relation})")
        
        # Step 1: Extract face embedding
        print("🔍 Extracting face embedding...")
        embedding = face_recognition.extract_embedding(request.image_base64)
        
        if embedding is None:
            raise HTTPException(
                status_code=400,
                detail="No face detected in the image. Please upload a clear photo showing the face.",
            )
        
        print(f"✅ Face embedding extracted (512-dim)")
        
        # Step 2: Create CONFIRMED person in Neo4j
        print("📝 Creating person in Neo4j...")
        person_id = graph_db.create_person(
            status="confirmed",
            name=request.name,
            relation=request.relation,
            contextual_note=request.contextual_note,
        )
        print(f"✅ Person created: {person_id}")
        
        # Step 3: Store face embedding in Qdrant
        print("📝 Storing face embedding in Qdrant...")
        vector_db.store_face_embedding(
            person_id=person_id,
            embedding=embedding,
            status="confirmed",
        )
        print(f"✅ Face embedding stored")
        
        # Step 4: Save face thumbnail
        print("📝 Saving face thumbnail...")
        os.makedirs(FACE_IMAGES_DIR, exist_ok=True)
        image = decode_base64_image(request.image_base64)
        image.thumbnail((200, 200))
        image_path = os.path.join(FACE_IMAGES_DIR, f"{person_id}.jpg")
        image.save(image_path, "JPEG", quality=85)
        print(f"✅ Face thumbnail saved")
        
        return EnrollPersonResponse(
            success=True,
            person_id=person_id,
            name=request.name,
            relation=request.relation,
            contextual_note=request.contextual_note,
            message=f"Successfully enrolled {request.name} ({request.relation})",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error enrolling person: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enroll person: {str(e)}",
        )


@router.get("/confirmed", response_model=ConfirmedPeopleResponse)
async def get_confirmed_people():
    """Get all confirmed people in the system."""
    confirmed = graph_db.get_confirmed_people()
    
    people = [
        ConfirmedPerson(
            person_id=p["id"],
            name=p.get("name", "Unknown"),
            relation=p.get("relation", "Unknown"),
            contextual_note=p.get("contextual_note"),
            face_image_url=f"/api/caregiver/face-image/{p['id']}",
        )
        for p in confirmed
    ]
    
    return ConfirmedPeopleResponse(confirmed_people=people)
