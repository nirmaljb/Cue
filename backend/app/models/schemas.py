"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


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
    emotionalCue: str
    familiarity: float
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
    """Request to enroll a new person (pre-enrollment by caregiver)."""
    name: str
    relation: str
    image_base64: str  # Photo of the person


class EnrollPersonResponse(BaseModel):
    """Response after enrolling a person."""
    status: str
    person_id: str
    name: str
    relation: str
    message: str


class ConfirmedPerson(BaseModel):
    """A confirmed person in the system."""
    person_id: str
    name: str
    relation: str
    face_image_url: str
    familiarity_score: float


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
