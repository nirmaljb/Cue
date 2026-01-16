# REMIND•AR — Dementia Face Recognition Assistant

> **"Observe first, remember later, assist once truth is confirmed."**

An AR-style face recognition system that helps dementia patients remember the people in their lives. The system observes faces, records interactions, and only displays identity information after a caregiver has confirmed who the person is.

## 🎯 Features

### Patient Mode
- **Real-time Face Detection** — MediaPipe-powered face tracking
- **AR-style HUD** — Glassmorphic overlay showing name, relation, and emotional cues
- **Memory Recording** — Audio recording with automatic transcription and summarization
- **Text-to-Speech** — Optional audio announcements for close family members

### Caregiver Mode
- **Review Pending People** — See all unconfirmed faces detected
- **Confirm Identities** — Assign names and relationships
- **Manage Memories** — View and edit recorded memories

## 🏗️ Architecture

```
Frontend (React/Vite)          Backend (FastAPI)
┌─────────────────────┐       ┌─────────────────────┐
│ Camera + MediaPipe  │──────▶│ FaceNet (512-dim)   │
│ HUD Overlay         │◀──────│ Groq LLM            │
│ Audio Recording     │──────▶│ Groq Whisper        │
│ Caregiver Panel     │◀─────▶│ Qdrant + Neo4j      │
└─────────────────────┘       └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Qdrant Cloud account
- Neo4j Cloud account
- Groq API key

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 3. Access the App

- **Patient Mode:** http://localhost:5173
- **Caregiver Mode:** http://localhost:5173/caregiver
- **API Docs:** http://localhost:8000/docs

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/recognize-face` | POST | Recognize a face from image |
| `/api/hud-context` | POST | Get HUD content for a person |
| `/api/memory/save` | POST | Save memory from audio |
| `/api/caregiver/pending` | GET | Get pending people |
| `/api/caregiver/confirm` | POST | Confirm a person's identity |

## 🔐 Key Principles

1. **No Identity Hallucination** — The LLM never guesses identities
2. **Caregiver Controls Truth** — Only caregivers can confirm identities
3. **TEMPORARY → CONFIRMED** — New faces start as temporary until reviewed
4. **Privacy by Design** — No passive surveillance, explicit recording only

## 📁 Project Structure

```
hackathon/
├── frontend/
│   ├── src/
│   │   ├── components/     # Camera, HUD, RecordButton
│   │   ├── hooks/          # useFaceTracking, useAudioRecorder
│   │   ├── pages/          # PatientMode, CaregiverMode
│   │   └── services/       # API client
│   └── ...
├── backend/
│   ├── app/
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # FaceNet, LLM, Whisper, DBs
│   │   └── models/         # Pydantic schemas
│   └── ...
└── plan.xml                # System design document
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + Vite |
| Face Tracking | MediaPipe |
| Backend | FastAPI |
| Face Recognition | FaceNet (facenet-pytorch) |
| LLM | Groq (llama-3.3-70b) |
| Speech-to-Text | Groq Whisper |
| Text-to-Speech | Web Speech API |
| Vector DB | Qdrant |
| Graph DB | Neo4j |

## 📄 License

MIT License — Built for hackathon demo purposes.
