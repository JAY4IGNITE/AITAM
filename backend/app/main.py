from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import investigations, websocket, auth

app = FastAPI(
    title="ThreatLens API",
    description="Risk-Adaptive Multi-Agent Phishing & Malicious Content Investigation Platform",
    version="1.0.0"
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
app.include_router(websocket.router, tags=["WebSockets"])

@app.on_event("startup")
async def startup_event():
    from .database.connection import engine
    from .models.base import Base
    
    # We now rely exclusively on Alembic for schema migrations instead of create_all
    # Ensure you run `alembic upgrade head` after docker-compose up
    pass

@app.get("/")
def root():
    return {"status": "ok", "message": "ThreatLens API is running"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
