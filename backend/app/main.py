from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import investigations, websocket, auth, threat_intel, incidents

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    import subprocess
    import sys
    print("Starting backend Celery worker...")
    worker_proc = subprocess.Popen([sys.executable, "-m", "celery", "-A", "app.worker.celery_app", "worker", "--loglevel=info", "-P", "threads"])
    
    yield
    
    print("Shutting down Celery worker...")
    worker_proc.terminate()

app = FastAPI(
    title="ThreatLens API",
    description="Risk-Adaptive Multi-Agent Phishing & Malicious Content Investigation Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(investigations.router, prefix="/api/investigations", tags=["Investigations"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(threat_intel.router, prefix="/api/threat-intel", tags=["Threat Intel"])
app.include_router(websocket.router, tags=["WebSockets"])

@app.get("/")
def root():
    return {"status": "ok", "message": "ThreatLens API is running"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
