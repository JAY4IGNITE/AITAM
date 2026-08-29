import os
import subprocess
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis import Redis

from .database.connection import engine, DATABASE_URL
from .models.base import Base
# Ensure all models are registered with Base.metadata
from .models import (
    Investigation, Finding, Evidence, AgentRun, SandboxSession,
    InvestigationEvent, IOC, Artifact, User, Alert, EvidenceNode, EvidenceEdge,
    AttackJourneyStep, RiskAssessment, TriageResult, InvestigationPlan,
    InvestigationTask, AgentMessage, ResponseAction, Incident,
    Dataset, DatasetSample, EvaluationRun, EvaluationResult, Report,
    AttackStep, ThreatReport, ThreatIndicator, TempMailInbox, TempMailMessage
)

from .api import (
    investigations, websocket, auth, threat_intel, incidents,
    datasets, evaluation, demo, dashboard, reports, education, tempmail
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Database Tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[ThreatLens API] Database schema synchronized successfully.")
    except Exception as e:
        print(f"[ThreatLens API] Database schema sync notice: {e}")

    # 2. Celery Worker Management (in container / local background)
    worker_proc = None
    if os.getenv("START_INLINE_CELERY", "false").lower() == "true":
        print("[ThreatLens API] Starting inline Celery worker...")
        worker_proc = subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "app.worker.celery_app",
            "worker", "--loglevel=info", "-P", "threads"
        ])
    
    yield
    
    if worker_proc:
        print("[ThreatLens API] Terminating inline Celery worker...")
        worker_proc.terminate()

app = FastAPI(
    title="ThreatLens API",
    description="Autonomous Multi-Agent Cybersecurity Investigation & Threat Intelligence Platform",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in origins else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(investigations.router, prefix="/api/investigations", tags=["Investigations"])
app.include_router(tempmail.router, prefix="/api/tempmail", tags=["TempMail Email Scanner"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(threat_intel.router, prefix="/api/threat-intel", tags=["Threat Intel"])
app.include_router(education.router, prefix="/api/education", tags=["Education"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["Evaluation"])
app.include_router(demo.router, prefix="/api/demo", tags=["Demo"])
app.include_router(websocket.router, tags=["WebSockets"])

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "ThreatLens API",
        "version": "2.0.0",
        "mode": "Autonomous Multi-Agent SOC"
    }

@app.get("/api/health")
async def health_check():
    import asyncpg
    from .engine.threat_intel_provider import registry
    from .engine.tempmail import tempmail_client
    from datetime import datetime
    
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "unhealthy",
            "redis": "unhealthy",
            "celery": "healthy",
            "sandbox": "healthy",
            "tempmail_so": "unhealthy",
            "threat_intel_providers": []
        }
    }
    
    # 1. Check PostgreSQL connection
    try:
        clean_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgres://").replace("postgresql://", "postgres://")
        conn = await asyncpg.connect(clean_url, timeout=3.0)
        await conn.execute("SELECT 1")
        await conn.close()
        status["services"]["database"] = "healthy"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["database"] = f"unhealthy ({str(e)})"
        
    # 2. Check Redis connection
    try:
        r = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_timeout=3.0)
        r.ping()
        status["services"]["redis"] = "healthy"
    except Exception as e:
        status["status"] = "degraded"
        status["services"]["redis"] = f"unhealthy ({str(e)})"

    # 3. Check Threat Intel Providers (URLhaus, VirusTotal, Google Safe Browsing, Local DB)
    try:
        health_list = await registry.get_health()
        status["services"]["threat_intel_providers"] = [h.model_dump() for h in health_list]
    except Exception:
        pass

    # 4. Check TempMail.so integration
    try:
        tm_health = await tempmail_client.health_check()
        status["services"]["tempmail_so"] = tm_health["status"]
    except Exception as e:
        status["services"]["tempmail_so"] = f"Degraded ({str(e)})"

    return status
