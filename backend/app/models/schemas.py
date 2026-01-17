"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class PersonStatus(str, Enum):
    """Status of a person in the system."""
    TEMPORARY = "temporary"
    CONFIRMED = "confirmed"


# ============================================
# Face Recognition Schemas
# ============================================

class RecognizeFaceRequest(BaseModel):
    """Request to recognize a face from images.
    
    Accepts multiple frames for better recognition quality.
    Backend will try each frame and return the best match.
    """
    images_base64: list[str]  # Array of base64 encoded images


class RecognizeFaceResponse(BaseModel):
    """Response from face recognition."""
    recognized: bool
    status: PersonStatus
    person_id: str
    confidence: Optional[float] = None
    message: Optional[str] = None


# ============================================
# HUD Context Schemas
# ============================================

class HUDContextRequest(BaseModel):
    """Request for HUD context for a person."""
    person_id: str
    status: PersonStatus


class HUDContextResponse(BaseModel):
    """HUD payload to display on frontend."""
    name: Optional[str] = None
    relation: Optional[str] = None
    contextual_note: Optional[str] = None
    # Removed emotionalCue and familiarity for Dementia-Safe design
    speak: bool = False
    speechText: Optional[str] = None


# ============================================
# Memory Schemas
# ============================================

class MemorySaveRequest(BaseModel):
    """Request to save a memory from audio recording."""
    person_id: str
    audio_base64: str


class MemorySaveResponse(BaseModel):
    """Response after saving a memory."""
    status: str
    memory_id: str
    summary: str
    emotional_tone: str


# ============================================
# Caregiver Schemas
# ============================================

class PendingPerson(BaseModel):
    """A pending temporary person awaiting confirmation."""
    person_id: str
    face_image_url: str
    interaction_count: int
    last_memory_summary: Optional[str] = None
    last_seen: str


class PendingPeopleResponse(BaseModel):
    """List of pending people for caregiver review."""
    pending_people: list[PendingPerson]


class ConfirmPersonRequest(BaseModel):
    """Request to confirm a temporary person's identity."""
    person_id: str
    name: str
    relation: str


class ConfirmPersonResponse(BaseModel):
    """Response after confirming a person."""
    status: str
    person_id: str
    message: str


class EnrollPersonRequest(BaseModel):
    """Request to enroll a new person."""
    name: str
    relation: str
    contextual_note: Optional[str] = None  # Static cue for the patient
    image_base64: str  # Photo of the person


class EnrollPersonResponse(BaseModel):
    """Response from enrolling a person."""
    success: bool
    person_id: str
    name: str
    relation: str
    contextual_note: Optional[str] = None
    message: str


class ConfirmedPerson(BaseModel):
    """A confirmed (enrolled) person."""
    person_id: str
    name: str
    relation: str
    contextual_note: Optional[str] = None
    face_image_url: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ConfirmedPeopleResponse(BaseModel):
    """List of confirmed people."""
    confirmed_people: list[ConfirmedPerson]


# ============================================
# Health Check Schema
# ============================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    qdrant: str
    neo4j: str
