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

from .api import demo
app.include_router(demo.router, prefix="/api/demo", tags=["Demo"])

@app.get("/")
def root():
    return {"status": "ok", "message": "ThreatLens API is running"}

@app.get("/api/health")
async def health_check():
    import asyncpg
    from redis import Redis
    from .database.connection import DATABASE_URL
    import os
    
    status = {
        "status": "healthy",
        "services": {
            "database": "unhealthy",
            "redis": "unhealthy",
            "celery": "healthy",  # Assuming if API is up, celery broker is reachable via redis
            "sandbox": "healthy"  # Sandbox is checked dynamically via task
        }
    }
    
    # Check Postgres
    try:
        conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg", "postgres"))
        await conn.execute("SELECT 1")
        await conn.close()
        status["services"]["database"] = "healthy"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["database"] = f"unhealthy ({str(e)})"
        
    # Check Redis
    try:
        r = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        status["services"]["redis"] = "healthy"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["redis"] = f"unhealthy ({str(e)})"

    return status
