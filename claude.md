# Cue (REMIND-AR) - Project Documentation for LLMs

This document provides a comprehensive overview of the Cue project for AI assistants like Claude to understand the codebase, architecture, and implementation details.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [Technology Stack](#technology-stack)
5. [Core Components](#core-components)
6. [API Endpoints](#api-endpoints)
7. [Data Flow](#data-flow)
8. [Key Features](#key-features)
9. [Design Principles](#design-principles)
10. [Setup & Configuration](#setup--configuration)
11. [Code Patterns](#code-patterns)

---

## Project Overview

**Cue** (formerly REMIND-AR) is a dementia care assistant that provides real-time face recognition and memory support for dementia patients. The system has two distinct modes:

- **Caregiver Mode**: Administrative interface for enrolling people and managing profiles
- **Patient Mode**: Real-time recognition interface that displays contextual information and records memories

### Core Problem Being Solved
Dementia patients struggle to recognize loved ones. Cue provides:
1. **Visual Cues**: Immediate display of name, relationship, and context when someone is recognized
2. **Audio Reassurance**: Gentle voice cue providing comfort ("This is Rahul, your grandson...") in 5 languages
3. **Memory Support**: Passive recording and summarization of conversations for later context
4. **Multi-Language**: Hindi, Tamil, Bengali, Telugu support via Sarvam AI

---

## Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│  ┌──────────────────┐       ┌─────────────────────────┐   │
│  │ Caregiver Mode   │       │    Patient Mode         │   │
│  │ (Setup/Admin)    │       │ (Real-time Recognition) │   │
│  └──────────────────┘       └─────────────────────────┘   │
└────────────────────┬────────────────────┬──────────────────┘
                     │                    │
                     ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Face Rec │  │   LLM    │  │   STT    │  │   TTS    │  │
│  │InsightFace│ │  (Groq)  │  │ (Groq)   │  │ElevenLabs│  │
│  └──────────┘  └──────────┘  └──────────┘  │ + Sarvam │  │
│                                             └──────────┘  │
└────────┬───────────────┬──────────────────────────────────┘
         │               │
         ▼               ▼
┌──────────────┐  ┌──────────────┐
│   Qdrant     │  │    Neo4j     │
│ (Vector DB)  │  │  (Graph DB)  │
│ - Faces      │  │ - Profiles   │
│ - Memories   │  │ - Memories   │
└──────────────┘  └──────────────┘
```

### Key Architectural Decisions

1. **Dual Database Strategy**:
   - **Qdrant**: Fast vector similarity search for face matching and semantic memory search
   - **Neo4j**: Graph database for relationships, metadata, and structured data

2. **Hybrid Processing**:
   - **Local**: InsightFace with ONNX (privacy, 5-10x faster than FaceNet)
   - **Cloud**: Groq LLM, Groq Whisper, ElevenLabs (quality, scalability)

3. **Real-time Loop**: 300ms face recognition polling with multi-frame validation

---

## Directory Structure

```
hackathon/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── CaregiverMode.jsx    # Admin panel
│   │   │   └── PatientMode.jsx      # Recognition interface
│   │   ├── components/
│   │   │   ├── HUD.jsx              # Heads-up display overlay
│   │   │   └── RecordButton.jsx     # Audio recording controls
│   │   ├── hooks/
│   │   │   ├── useFaceTracking.js   # Face recognition loop
│   │   │   └── useAudioRecorder.js  # Memory recording
│   │   └── services/
│   │       └── api.js               # Backend API calls
│   └── vite.config.js
│
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry
│   │   ├── config.py                # Environment config
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic models
│   │   ├── routers/
│   │   │   ├── recognize.py         # Face recognition endpoint
│   │   │   ├── hud.py               # HUD context endpoint (multi-lang)
│   │   │   ├── whisper.py           # Audio cue endpoint (multi-lang)
│   │   │   ├── memory.py            # Memory save endpoint
│   │   │   └── caregiver.py         # CRUD for people
│   │   ├── services/
│   │   │   ├── face_recognition.py  # InsightFace wrapper
│   │   │   ├── vector_db.py         # Qdrant client
│   │   │   ├── graph_db.py          # Neo4j client
│   │   │   ├── llm.py               # Groq LLM service
│   │   │   ├── sarvam.py            # Sarvam Translate + TTS
│   │   │   ├── whisper.py           # Groq STT service
│   │   │   ├── elevenlabs.py        # ElevenLabs TTS (English)
│   │   │   └── routine.py           # Routine extraction
│   │   ├── workers/
│   │   │   └── routine_worker.py    # Background routine extraction
│   │   ├── data/
│   │   │   ├── relations.py         # Multi-lang relation dictionary
│   │   │   └── whisper_templates.py # Audio templates per language
│   │   └── utils/
│   │       └── image.py             # Image processing
│   └── requirements.txt
│
└── face_images/              # Stored face thumbnails
```

---

## Technology Stack

### Frontend
- **React 18** (Vite) - UI framework
- **MediaPipe** - Real-time face detection in browser
- **Web Audio API** - Microphone recording

### Backend
- **FastAPI** - Async Python web framework
- **InsightFace** (buffalo_s model) - Face embedding extraction (512-dim, ONNX-accelerated)
- **Groq API**:
  - `llama-3.3-70b-versatile` - LLM for content generation
  - `whisper-large-v3` - Speech-to-text transcription
- **ElevenLabs** - Text-to-speech (Jyot voice) for English audio cues
- **Sarvam AI** - Indian language TTS (Vidya voice) + Translation (mayura:v1)
- **SentenceTransformers** - Memory embedding (all-MiniLM-L6-v2, 384-dim)

### Databases
- **Qdrant Cloud** - Vector similarity search
- **Neo4j Cloud** - Graph database

### Platform Support
| Platform | CPU | GPU | Notes |
|----------|-----|-----|-------|
| macOS (Apple Silicon) | ✅ | ✅ CoreML | Best performance |
| macOS (Intel) | ✅ | ❌ | CPU only |
| Windows | ✅ | ✅ CUDA | Install `onnxruntime-gpu` |
| Linux | ✅ | ✅ CUDA | Install `onnxruntime-gpu` |

---

## Core Components

### Frontend Components

#### 1. `PatientMode.jsx` - The Main Experience
**Purpose**: Real-time face recognition and memory recording

**Key State**:
- `isRecognized`: Person detected state
- `currentPersonId`: Matched person ID
- `hudData`: Profile data for display
- `isRecording`: Microphone state

**Hooks Used**:
- `useFaceTracking()`: 300ms recognition loop
- `useAudioRecorder()`: Memory recording

**Flow**:
```javascript
useEffect(() => {
  if (isRecognized && currentPersonId) {
    // 1. Fetch HUD data
    fetchHUD();
    
    // 2. Play whisper (if enabled)
    if (whisperEnabled) {
      setTimeout(() => fetchAndPlayWhisper(), 400);
    }
    
    // 3. Start recording (if enabled)
    if (autoRecordEnabled) {
      startRecording();
    }
  }
}, [isRecognized, currentPersonId]);
```

#### 2. `CaregiverMode.jsx` - The Admin Panel
**Purpose**: Enroll, edit, and manage known people

**Key Features**:
- Enrollment form with webcam/upload
- People grid (Bento layout)
- Edit modal
- Delete with confirmation
- Settings toggles (Memories, Whisper)

**State Management**:
- `confirmedPeople`: List of enrolled people
- `showEnrollForm`: Toggle enrollment UI
- `editingPerson`: Currently editing person
- `autoRecordEnabled`, `whisperEnabled`: Feature toggles

#### 3. `useFaceTracking.js` - Recognition Loop
**Purpose**: Continuous face detection and recognition

**Key Logic**:
```javascript
// Every 300ms:
1. Capture video frame
2. Detect faces using MediaPipe
3. Send frames to /api/recognize-face
4. Update isRecognized, currentPersonId
5. If face lost for 5s → mark as idle
```

**States**:
- `isIdle`: No face detected
- `isRecognized`: Known person detected
- `isNotFound`: Unknown person detected

#### 4. `HUD.jsx` - Visual Overlay
**Purpose**: Display person info over video

**Positioning**:
- Simple offset: 80px right, 100px up from face center
- Smoothing handled by Lerp in `useFaceTracking.js`
- High contrast for readability

**Styling**:
- Name: Large, bold text
- Relation: Green pill badge (#8DA399)
- Semi-transparent white background

### Backend Services

#### 1. `face_recognition.py` - InsightFace Service
**Key Methods**:
- `extract_embedding(image_base64)`: Base64 → PIL → Face Detection → 512-dim vector
- `extract_embedding_from_pil(image)`: PIL Image → Face Detection → 512-dim vector

**Model**: InsightFace buffalo_s (ONNX runtime)
**Performance**: 
- Mac (CoreML): ~100-150ms per frame
- Windows (CUDA GPU): ~20-50ms per frame
- CPU fallback: ~200-300ms per frame

**Device Selection**: Automatically uses best available (CUDA → CoreML → CPU)

#### 2. `vector_db.py` - Qdrant Service
**Collections**:
1. `face_embeddings` (512-dim)
   - Payload: `person_id`, `status` (confirmed/temporary)
2. `memory_embeddings` (384-dim)
   - Payload: `person_id`, `summary`, `emotional_tone`

**Key Methods**:
- `search_face(embedding, limit=5)`: Find matching faces
- `store_face_embedding(person_id, embedding, status)`
- `store_memory_embedding(memory_id, person_id, embedding, ...)`

#### 3. `graph_db.py` - Neo4j Service
**Node Types**:
- `Person`: {id, name, relation, contextual_note, status, familiarity, last_seen}
- `Memory`: {id, summary, emotional_tone, important_event, raw_transcript, timestamp}
- `Routine`: {id, text, confidence, source, created_at}

**Relationships**:
- `(Person)-[:HAS_MEMORY]->(Memory)`
- `(Person)-[:HAS_ROUTINE]->(Routine)`

**Key Methods**:
- `create_person(person_id, name, relation, ...)`
- `update_person(person_id, name=None, relation=None, ...)`
- `get_person(person_id)` → Returns person dict
- `create_memory(person_id, summary, emotional_tone, ...)`
- `get_memories(person_id, limit=10)`

#### 4. `llm.py` - Groq LLM Service
**Model**: `llama-3.3-70b-versatile` via Groq API

**Methods**:

1. **`generate_hud_context(name, relation, memories, familiarity_score)`**
   - Currently returns static data (HUD is dementia-safe, no AI hallucination)

2. **`summarize_memory(transcript)`**
   - Input: Raw conversation text
   - Output: `{summary, emotional_tone, important_event}`
   - Temperature: 0.4 (consistency)

3. **`generate_whisper_text(name, relation, contextual_note, recent_memory)`**
   - Input: Person data + latest memory
   - Output: 1-2 sentence calm reassurance (fallback)

4. **`generate_whisper(name, relation, routines, contextual_note)`** (NEW)
   - Input: Person data + database routines
   - Output: 4-sentence comfort message with routines
   - Structure:
     1. "This is [name]. He's/She's your [relation]."
     2. Comfort statement
     3. Routine/shared activity
     4. Reassurance ("You can take your time." / "You're safe here." / "There's no rush.")

5. **`extract_routines_from_memories(memories)`** (NEW)
   - Input: List of memory summaries
   - Output: JSON array of extracted routine patterns
   - Returns specific, concrete routines (not generic statements)

6. **`select_best_routine(routines, recent_memory)`** (NEW)
   - Selects most relevant routine for HUD display

**System Messages**:
- HUD: "You are a calm, supportive assistant helping dementia patients..."
- Memory: "You are a memory summarization assistant. Create concise, gentle summaries..."
- Whisper: "You are a calm, warm voice providing gentle reassurance..."

#### 5. `whisper.py` (STT Service)
**API**: Groq Whisper API (`whisper-large-v3`)

**Flow**:
```python
def transcribe(audio_base64):
    1. Decode base64 → bytes
    2. Write to temp file (Groq requires file input)
    3. Call Groq API
    4. Return transcript text
    5. Delete temp file
```

#### 6. `elevenlabs.py` (TTS Service)
**API**: ElevenLabs Text-to-Speech

**Voice**: Jyot (6kUBvNdOU57rLktR7BK5) - Smooth, comforting female voice

**Settings**: Default ElevenLabs settings (natural, clear speech)

**Output**: MP3 audio bytes (base64 encoded for frontend)

#### 7. `routine.py` (Routine Extraction Service) (NEW)
**Purpose**: Extract routine patterns from conversation memories

**Key Function**: `analyze_and_update_routines(person_id)`
- Fetches all memories for person
- Uses LLM to extract specific, concrete patterns
- Stores routines in Neo4j as `Routine` nodes
- Triggered by background worker every 2 memories

### Background Worker

#### `workers/routine_worker.py` (NEW)
**Purpose**: Isolated background process for routine extraction

**Polling**: Every 30 seconds
**Logic**:
1. Query Neo4j for people needing routine analysis
2. Check: memory_count % 2 == 0 AND last_routine_analysis < last_memory_saved
3. Run routine extraction for each person
4. Mark analysis complete

---

## API Endpoints

### Face Recognition
```
POST /api/recognize-face
Body: { images_base64: string[] }
Response: { 
  recognized: bool,
  status: "confirmed" | "temporary",
  person_id: string,
  confidence: float,
  message: string
}
```

**Logic**:
1. Try each frame (multi-frame validation)
2. Extract embedding for each
3. Search Qdrant for best match
4. Return only if status="confirmed" and confidence > threshold

### HUD Context
```
POST /api/hud-context
Body: { person_id: string, status: string }
Response: {
  name: string,
  relation: string,
  contextual_note: string,
  speak: bool,
  speechText: string
}
```

**Logic**:
- If status="temporary" → return empty (dementia-safe silence)
- If status="confirmed" → fetch from Neo4j and return static data

### Audio Whisper
```
GET /api/whisper/{person_id}
Response: {
  audio_url: string (base64 data URI),
  text: string,
  reason?: string
}
```

**Logic**:
1. Fetch person from Neo4j
2. Fetch 1 recent memory
3. LLM generates script
4. ElevenLabs converts to audio
5. Return base64 MP3
6. On any failure → silent (audio_url: null)

### Memory Save
```
POST /api/memory/save
Body: { person_id: string, audio_base64: string }
Response: {
  status: "saved",
  memory_id: string,
  summary: string,
  emotional_tone: string
}
```

**Logic**:
1. Groq Whisper transcribes audio
2. LLM summarizes transcript
3. Store in Neo4j (graph node)
4. Generate embedding (SentenceTransformer)
5. Store in Qdrant (vector)

### Caregiver CRUD
```
POST /api/caregiver/enroll
Body: { name, relation, contextual_note, image_base64 }
Response: { person_id, status: "enrolled" }

PUT /api/caregiver/person/{person_id}
Body: { name?, relation?, contextual_note?, image_base64? }
Response: { status: "updated" }

DELETE /api/caregiver/person/{person_id}
Response: { status: "deleted", person_id }

GET /api/caregiver/confirmed
Response: { confirmed_people: Person[] }
```

---

## Data Flow

### 1. Enrollment Flow
```
Caregiver Input (Name, Relation, Photo)
         ↓
   POST /caregiver/enroll
         ↓
   FaceNet: Photo → 512-dim embedding
         ↓
   ┌─────────────┬──────────────┐
   ↓             ↓              ↓
Qdrant        Neo4j         File System
(vector)     (metadata)     (thumbnail)
```

### 2. Recognition Flow
```
Video Frame (300ms)
         ↓
   POST /recognize-face
         ↓
   FaceNet: Frame → embedding
         ↓
   Qdrant: Vector search
         ↓
   Match? → person_id
         ↓
   POST /hud-context
         ↓
   Neo4j: Fetch profile
         ↓
   Display HUD
```

### 3. Whisper Flow
```
Recognition Event
         ↓
   Wait 400ms (calm transition)
         ↓
   GET /whisper/{person_id}
         ↓
   Neo4j: Profile + Recent Memory
         ↓
   LLM (GPT-OSS-120b): Generate script
         ↓
   ElevenLabs: Text → Audio
         ↓
   Play MP3 (volume 0.6)
```

### 4. Memory Flow
```
Face Recognized → Mic ON
Face Lost → Mic OFF
         ↓
   POST /memory/save
         ↓
   ┌──────────────┬───────────────┐
   ↓              ↓               ↓
Groq Whisper   LLM Summary   SentenceTransformer
(transcribe)   (summarize)   (embed)
   ↓              ↓               ↓
   └──────────────┴───────────────┘
         ↓
   ┌─────────────┬──────────────┐
   ↓             ↓              
Neo4j         Qdrant          
(graph node)  (vector)
```

---

## Key Features

### 1. Face Recognition (Multi-Frame Validation)
- Captures 3 frames
- Processes each independently
- Returns best match
- Confidence threshold: 0.6
- Only returns "confirmed" status people

### 2. Visual HUD (Dementia-Safe)
- **Static Data**: No AI generation (zero hallucination risk)
- **High Contrast**: Black text on semi-opaque white background
- **Positioned**: Offset from face to avoid overlap
- **Persistent**: Stays visible while face is detected

### 3. Audio Whisper (Gentle Reassurance)
- **One-Time**: Plays once per session
- **Delayed**: 400ms after recognition (calm transition)
- **LLM-Generated**: Personalized using profile + recent memory
- **Toggleable**: Caregiver can disable
- **Silent Failure**: No audio if any step fails

### 4. Passive Memory Recording
- **Automatic**: Starts on recognition (if enabled)
- **Hands-Free**: No button press needed
- **Smart Stop**: Stops when face leaves frame
- **Summarized**: LLM extracts key points
- **Searchable**: Vector embedding for future semantic search

### 5. Profile Editing
- **Edit in Place**: Modal overlay for quick updates
- **Photo Update**: Can replace face photo (re-generates embedding)
- **Immediate Sync**: Updates both Neo4j and Qdrant
- **Confirmation**: Delete requires confirmation dialog

---

## Design Principles

### Dementia-Safe Design
1. **Calm Over Cleverness**: Predictable, not surprising
2. **Stability Over Responsiveness**: Consistent UI, no sudden changes
3. **Familiarity Over Novelty**: High-contrast text, simple layouts
4. **Visual First**: HUD is static and instant
5. **Audio Second**: Whisper is gentle and optional

### Privacy & Control
- **Caregiver Authority**: Only caregivers can enroll/edit
- **Toggle Controls**: Caregivers control recording and whisper
- **Local Storage**: Preferences persist on device
- **No Cloud Storage**: Face images stored locally on server

### Performance
- **Real-time Recognition**: 300ms loop
- **Immediate HUD**: <100ms display
- **Calm Audio**: 400ms delay (intentional)
- **Background Processing**: Memory save non-blocking

---

## Setup & Configuration

### Environment Variables

**Frontend** (`.env`):
```
VITE_API_URL=http://localhost:8000/api
```

**Backend** (`.env`):
```
# Groq API
GROQ_API_KEY=gsk_...

# Qdrant Cloud
QDRANT_URL=https://...
QDRANT_API_KEY=...

# Neo4j Cloud
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...

# ElevenLabs
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Config
FACE_SIMILARITY_THRESHOLD=0.8
```

### Installation

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

**Backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

---

## Code Patterns

### Frontend Patterns

#### 1. API Calls (services/api.js)
```javascript
export async function recognizeFace(imagesBase64) {
  const response = await fetch(`${API_URL}/recognize-face`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ images_base64: imagesBase64 }),
  });
  if (!response.ok) throw new Error('Recognition failed');
  return response.json();
}
```

#### 2. Custom Hooks (useFaceTracking.js)
```javascript
export function useFaceTracking(videoRef, onRecognize) {
  const [isRecognized, setIsRecognized] = useState(false);
  const [currentPersonId, setCurrentPersonId] = useState(null);
  
  useEffect(() => {
    // 300ms recognition loop
    const interval = setInterval(async () => {
      const frames = captureFrames(videoRef.current);
      const result = await recognizeFace(frames);
      if (result.recognized) {
        setIsRecognized(true);
        setCurrentPersonId(result.person_id);
        onRecognize(result);
      }
    }, 300);
    
    return () => clearInterval(interval);
  }, []);
  
  return { isRecognized, currentPersonId, ... };
}
```

#### 3. LocalStorage for Toggles
```javascript
const [whisperEnabled, setWhisperEnabled] = useState(() => {
  return localStorage.getItem('cue_whisperEnabled') !== 'false';
});

const toggleWhisper = () => {
  const newValue = !whisperEnabled;
  setWhisperEnabled(newValue);
  localStorage.setItem('cue_whisperEnabled', String(newValue));
};
```

### Backend Patterns

#### 1. Service Singletons
```python
class FaceRecognitionService:
    def __init__(self):
        self.model = None
        self._initialized = False
    
    def initialize(self):
        if self._initialized:
            return
        self.model = InceptionResnetV1(pretrained='vggface2').eval()
        self._initialized = True

# Singleton
face_recognition = FaceRecognitionService()
```

#### 2. Router Pattern
```python
router = APIRouter(tags=["Memory"])

@router.post("/memory/save", response_model=MemorySaveResponse)
async def save_memory(request: MemorySaveRequest):
    # Business logic
    transcript = whisper_service.transcribe(request.audio_base64)
    memory_data = llm_service.summarize_memory(transcript)
    memory_id = graph_db.create_memory(...)
    return MemorySaveResponse(...)
```

#### 3. Error Handling (Silent Failures)
```python
try:
    audio_bytes = await generate_speech(whisper_text)
    if not audio_bytes:
        return WhisperResponse(reason="tts_failed")
except Exception as e:
    print(f"⚠️ Whisper error: {e}")
    return WhisperResponse(reason="generation_failed")
```

---

## Common Tasks

### Adding a New Feature

1. **Update Task List**: `brain/task.md`
2. **Backend**:
   - Add endpoint to `app/routers/`
   - Add service to `app/services/` if needed
   - Update schemas in `app/models/schemas.py`
   - Register router in `app/main.py`
3. **Frontend**:
   - Add API function to `services/api.js`
   - Update component (PatientMode or CaregiverMode)
   - Add CSS to corresponding `.css` file

### Debugging Recognition Issues

1. **Check Console Logs**:
   - Frontend: "🔍 Processing X frames..."
   - Backend: "Frame 1: Matched ... (confidence: 0.XX)"

2. **Verify Database**:
   - Qdrant: Check collection size
   - Neo4j: Query Person nodes

3. **Test Embedding**:
   - Use `/api/recognize-face` with test image
   - Check confidence scores

### Modifying LLM Behavior

Edit `backend/app/services/llm.py`:
- Adjust `temperature` (lower = more consistent)
- Modify system message
- Change prompt structure
- Update `max_tokens`

---

## Common Issues & Solutions

### 1. "BaseModel not defined"
**Cause**: Import order issue
**Fix**: Ensure `from pydantic import BaseModel` is at top of file

### 2. Recognition not working
**Causes**:
- Webcam not accessible
- Face too small/blurry
- Person not enrolled
- Qdrant not connected

**Debug**:
```bash
# Check Qdrant connection
curl http://localhost:8000/api/health

# Check enrollment
curl http://localhost:8000/api/caregiver/confirmed
```

### 3. Whisper audio not playing
**Causes**:
- Toggle disabled
- ElevenLabs API key missing
- Browser autoplay policy

**Check**:
- `localStorage.getItem('cue_whisperEnabled')`
- Backend logs for ElevenLabs errors
- Browser console for audio errors

### 4. Memory not saving
**Causes**:
- Groq API key missing
- Audio recording failed
- Neo4j not connected

**Debug**: Check backend logs for transcription/summarization errors

---

## Testing Checklist

### Caregiver Mode
- [ ] Enroll person with webcam
- [ ] Enroll person with file upload
- [ ] Edit person name/relation/note
- [ ] Edit person photo (verify re-embedding)
- [ ] Delete person (verify from both DBs)
- [ ] Toggle "Memories" on/off
- [ ] Toggle "Whisper" on/off

### Patient Mode
- [ ] Face recognized within 2 seconds
- [ ] HUD displays correct name/relation
- [ ] Whisper plays after 400ms (if enabled)
- [ ] Recording starts on recognition (if enabled)
- [ ] Recording stops when face leaves
- [ ] Memory saved and appears in Neo4j

---

## Codebase Quick Reference

### Key Files to Understand First
1. `frontend/src/pages/PatientMode.jsx` - Main user experience
2. `backend/app/main.py` - API structure
3. `backend/app/services/face_recognition.py` - Face matching
4. `backend/app/services/llm.py` - Content generation
5. `frontend/src/hooks/useFaceTracking.js` - Recognition loop

### File Location Quick Lookup
| Component | File Path |
|-----------|-----------|
| Recognition Loop | `frontend/src/hooks/useFaceTracking.js` |
| Visual HUD | `frontend/src/components/HUD.jsx` |
| Memory Recording | `frontend/src/hooks/useAudioRecorder.js` |
| Face API | `backend/app/routers/recognize.py` |
| Whisper API | `backend/app/routers/whisper.py` |
| Memory API | `backend/app/routers/memory.py` |
| Caregiver API | `backend/app/routers/caregiver.py` |
| FaceNet Service | `backend/app/services/face_recognition.py` |
| Qdrant Service | `backend/app/services/vector_db.py` |
| Neo4j Service | `backend/app/services/graph_db.py` |
| LLM Service | `backend/app/services/llm.py` |
| STT Service | `backend/app/services/whisper.py` |
| TTS Service | `backend/app/services/elevenlabs.py` |

---

This document should give you (Claude or any LLM) a complete understanding of the Cue codebase. For specific implementation details, refer to the actual code files mentioned above.
