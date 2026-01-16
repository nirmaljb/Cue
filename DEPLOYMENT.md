# Deployment Guide

## Backend → Render

### Quick Deploy (Recommended)

1. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/cue.git
   git push -u origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com) and sign up

3. **Deploy Backend**
   - Click **New** → **Web Service**
   - Connect your GitHub repo
   - Render will auto-detect `render.yaml`
   - Or manually configure:
     - **Root Directory**: `backend`
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables**
   In Render dashboard → Environment:
   ```
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your-api-key
   NEO4J_URI=neo4j+s://your-instance.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   GROQ_API_KEY=your-groq-key
   FACE_SIMILARITY_THRESHOLD=0.6
   ```

5. **Deploy**
   - Click **Create Web Service**
   - Wait ~3-5 minutes for build
   - Your backend will be at: `https://cue-backend.onrender.com`

### Important Notes

- **Free tier**: Spins down after 15 min idle → first request takes ~30s
- **Paid tier** ($7/mo): Stays warm, instant responses
- **For demo**: Hit `/api/health` before presenting to warm up

---

## Frontend → Vercel

1. **Go to [vercel.com](https://vercel.com)** and sign up

2. **Import Project**
   - Click **Add New** → **Project**
   - Import from GitHub

3. **Configure**
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. **Environment Variable**
   ```
   VITE_API_URL=https://cue-backend.onrender.com/api
   ```

5. **Deploy**
   - Click **Deploy**
   - Your frontend will be at: `https://cue.vercel.app`

---

## Post-Deployment Checklist

- [ ] Test `/api/health` on backend
- [ ] Test face enrollment in caregiver panel
- [ ] Test face recognition in patient mode
- [ ] Verify Qdrant and Neo4j connections
