"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.models.schemas import HealthResponse
from app.services.vector_db import vector_db
from app.services.graph_db import graph_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Connect to databases
    print("🚀 Starting REMIND-AR Backend...")
    try:
        vector_db.connect()
        print("✅ Connected to Qdrant")
    except Exception as e:
        print(f"⚠️ Qdrant connection failed: {e}")
    
    try:
        graph_db.connect()
        print("✅ Connected to Neo4j")
    except Exception as e:
        print(f"⚠️ Neo4j connection failed: {e}")
    
    print("🎯 REMIND-AR Backend ready!")
    
    yield
    
    # Shutdown: Close connections
    print("👋 Shutting down REMIND-AR Backend...")
    graph_db.close()


app = FastAPI(
    title="REMIND-AR API",
    description="Dementia Face Recognition Assistant Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify all services are running."""
    qdrant_status = "connected" if vector_db.health_check() else "disconnected"
    neo4j_status = "connected" if graph_db.health_check() else "disconnected"
    
    overall_status = "ok" if qdrant_status == "connected" and neo4j_status == "connected" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        qdrant=qdrant_status,
        neo4j=neo4j_status,
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "REMIND-AR API",
        "version": "1.0.0",
        "description": "Dementia Face Recognition Assistant",
    }


# Import and include routers
from app.routers import recognize, hud, memory, caregiver
app.include_router(recognize.router, prefix="/api")
app.include_router(hud.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(caregiver.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
