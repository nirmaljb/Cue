# Cue — Real-time Augmented Memory for dementia patients

> **"Dementia takes away the context. We give you the Cue"**

Real-time Augmented Memory for dementia patients, powered by edge-AI face tracking (MediaPipe) and semantic vector search (Qdrant) to deliver instant, context-aware recognition.

## 🎯 Features

### Patient Mode
- **Real-time Face Detection** — MediaPipe-powered face tracking
- **AR-style HUD** — Glassmorphic overlay showing name, relation, and routine activities
- **Memory Recording** — Audio recording with automatic transcription and summarization
- **Enhanced Audio Cues** — 4-sentence comfort whispers via ElevenLabs/Sarvam AI
- **Routine Extraction** — AI-detected patterns from conversations shown in HUD
- **Multi-Language Support** — English, Hindi, Tamil, Bengali, Telugu

### Caregiver Mode
- **Review Pending People** — See all unconfirmed faces detected
- **Confirm Identities** — Assign names and relationships
- **Manage Memories** — View and edit recorded memories
- **Language Selection** — Choose display/audio language for patient

## 🏗️ Architecture

```
Frontend (React/Vite)          Backend (FastAPI)
┌─────────────────────┐       ┌─────────────────────┐
│ Camera + MediaPipe  │──────▶│ InsightFace (ONNX)  │
│ HUD Overlay         │◀──────│ Groq LLM            │
│ Audio Recording     │──────▶│ Groq Whisper        │
│ Caregiver Panel     │◀─────▶│ Qdrant + Neo4j      │
└─────────────────────┘       │ ElevenLabs + Sarvam │
                              └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+ (3.11 recommended)
- Qdrant Cloud account
- Neo4j Cloud account
- API Keys: Groq, ElevenLabs, Sarvam AI

---

### 1. Backend Setup

#### macOS / Linux

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (see Environment Variables below)

# Run the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# (Optional) Run background worker for routine extraction
python -m app.workers.routine_worker
```

#### Windows

```powershell
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies (with CUDA support for GPU acceleration)
pip install -r requirements.txt

# For GPU acceleration (optional, requires CUDA 11.x):
pip uninstall onnxruntime
pip install onnxruntime-gpu

# Copy and configure environment
copy .env.example .env
# Edit .env with your API keys

# Run the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# (Optional) Run background worker for routine extraction
python -m app.workers.routine_worker
```

> **Note for Windows GPU Users:** InsightFace uses ONNX Runtime. Install `onnxruntime-gpu` for CUDA acceleration (5-10x faster face recognition).

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

---

### 3. Environment Variables

Create `backend/.env` with these keys:

```env
# Required
GROQ_API_KEY=your_groq_api_key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# TTS (Text-to-Speech)
ELEVENLABS_API_KEY=your_elevenlabs_key  # For English
SARVAM_API_KEY=your_sarvam_key          # For Hindi, Tamil, Bengali, Telugu
```

---

### 4. Access the App

- **Patient Mode:** http://localhost:5173
- **Caregiver Mode:** http://localhost:5173/caregiver
- **API Docs:** http://localhost:8000/docs

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/recognize-face` | POST | Recognize a face from image |
| `/api/hud-context?lang=` | POST | Get HUD content (with language) |
| `/api/whisper/{id}?lang=` | GET | Generate audio whisper cue |
| `/api/memory/save` | POST | Save memory from audio |
| `/api/caregiver/pending` | GET | Get pending people |
| `/api/caregiver/confirm` | POST | Confirm a person's identity |

## 🌐 Supported Languages

| Language | Code | TTS Provider | Voice |
|----------|------|--------------|-------|
| English | `en` | ElevenLabs | Jyot |
| Hindi | `hi` | Sarvam AI | Vidya |
| Tamil | `ta` | Sarvam AI | Vidya |
| Bengali | `bn` | Sarvam AI | Vidya |
| Telugu | `te` | Sarvam AI | Vidya |

## 🔐 Key Principles

1. **No Identity Hallucination** — The LLM never guesses identities
2. **Caregiver Controls Truth** — Only caregivers can confirm identities
3. **TEMPORARY → CONFIRMED** — New faces start as temporary until reviewed
4. **Privacy by Design** — No passive surveillance, explicit recording only
5. **Respectful Language** — Uses formal pronouns (आप/நீங்கள்/আপনি/మీరు)

## 📁 Project Structure

```
hackathon/
├── frontend/
│   ├── src/
│   │   ├── components/     # Camera, HUD, LanguageSelector
│   │   ├── hooks/          # useFaceTracking, useAudioRecorder
│   │   ├── pages/          # PatientMode, CaregiverMode
│   │   └── services/       # API client
│   └── ...
├── backend/
│   ├── app/
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # InsightFace, LLM, Sarvam, Whisper, DBs
│   │   ├── workers/        # Background routine worker
│   │   ├── data/           # Relations dictionary, templates
│   │   └── models/         # Pydantic schemas
│   └── ...
└── claude.md               # System design document
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + Vite |
| Face Tracking | MediaPipe (Browser) |
| Backend | FastAPI |
| Face Recognition | InsightFace (buffalo_s, ONNX) |
| LLM | Groq (llama-3.3-70b-versatile) |
| Speech-to-Text | Groq Whisper |
| Text-to-Speech | ElevenLabs (English) + Sarvam AI (Indian languages) |
| Translation | Sarvam AI (mayura:v1) |
| Vector DB | Qdrant Cloud |
| Graph DB | Neo4j Cloud |

## 🖥️ Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| macOS (Apple Silicon) | ✅ Full | CoreML acceleration for ONNX |
| macOS (Intel) | ✅ Full | CPU-based ONNX |
| Windows (NVIDIA GPU) | ✅ Full | Install `onnxruntime-gpu` for CUDA |
| Windows (CPU) | ✅ Full | Slower face recognition |
| Linux | ✅ Full | GPU support with CUDA |

## 📄 License

MIT License — Built for hackathon demo purposes.
