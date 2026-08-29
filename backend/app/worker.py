import os
import asyncio
import httpx
from datetime import datetime
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.future import select

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("threatlens_backend", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
)

@celery_app.task(name="execute_agent_task", bind=True, max_retries=3)
def execute_agent_task(self, investigation_id: str, agent_name: str, payload: dict):
    # Start asyncio event loop to run the async agent
    return asyncio.run(_run_agent(investigation_id, agent_name, payload))

@celery_app.task(name="sync_threat_intel_feed_task", bind=True, max_retries=2)
def sync_threat_intel_feed_task(self):
    return asyncio.run(_sync_urlhaus_feed())

@celery_app.task(name="poll_tempmail_inbox_task", bind=True, max_retries=3)
def poll_tempmail_inbox_task(self, inbox_id: str):
    return asyncio.run(_poll_tempmail_inbox(inbox_id))

@celery_app.task(name="poll_all_tempmail_inboxes_task", bind=True, max_retries=2)
def poll_all_tempmail_inboxes_task(self):
    return asyncio.run(_poll_all_tempmail_inboxes())

async def _run_agent(investigation_id: str, agent_name: str, payload: dict):
    from .agents.base import BaseAgent
    # Ensure all agents are loaded
    from .agents import (
        url_agent, content_agent, brand_agent, threat_intel, phishing_agent,
        email_agent, sms_agent, social_agent, triage_agent, investigation_planner,
        response_agent, incident_summarization, qr_agent, qr_processor,
        behavior_agent, sandbox_agent
    )
    
    agent_classes = {cls.__name__: cls for cls in BaseAgent.__subclasses__()}
    if agent_name not in agent_classes:
        return {"status": "FAILED", "error": f"Agent {agent_name} not found"}
        
    agent_class = agent_classes[agent_name]
    
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/threatlens")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    local_engine = create_async_engine(db_url, poolclass=NullPool)
    LocalSession = async_sessionmaker(local_engine, expire_on_commit=False)
    
    async with LocalSession() as session:
        try:
            result = await agent_class.analyze(investigation_id, session)
            return {"status": "COMPLETED", "result": result.model_dump(mode='json')}
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
        finally:
            await local_engine.dispose()

async def _poll_tempmail_inbox(inbox_id: str) -> dict:
    from .engine.tempmail_ingestion import TempMailIngestionService
    
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/threatlens")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    local_engine = create_async_engine(db_url, poolclass=NullPool)
    LocalSession = async_sessionmaker(local_engine, expire_on_commit=False)
    
    async with LocalSession() as session:
        try:
            return await TempMailIngestionService.poll_inbox(inbox_id, session)
        except Exception as e:
            return {"status": "FAILED", "error": str(e)}
        finally:
            await local_engine.dispose()

async def _poll_all_tempmail_inboxes() -> list:
    from .engine.tempmail_ingestion import TempMailIngestionService
    
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/threatlens")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    local_engine = create_async_engine(db_url, poolclass=NullPool)
    LocalSession = async_sessionmaker(local_engine, expire_on_commit=False)
    
    async with LocalSession() as session:
        try:
            return await TempMailIngestionService.poll_all_active_inboxes(session)
        except Exception as e:
            return [{"status": "FAILED", "error": str(e)}]
        finally:
            await local_engine.dispose()

async def _sync_urlhaus_feed() -> dict:
    from .models.threat_intel import ThreatIndicator
    
    auth_key = os.getenv("URLHAUS_AUTH_KEY") or os.getenv("URLHAUS_API_KEY", "")
    headers = {"User-Agent": "ThreatLens-Feed-Sync/2.0"}
    if auth_key:
        headers["Auth-Key"] = auth_key
        
    url = "https://urlhaus-api.abuse.ch/v1/urls/recent/"
    
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/threatlens")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    local_engine = create_async_engine(db_url, poolclass=NullPool)
    LocalSession = async_sessionmaker(local_engine, expire_on_commit=False)
    
    new_count = 0
    updated_count = 0
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            
        if resp.status_code != 200:
            return {"status": "FAILED", "error": f"URLhaus API returned HTTP {resp.status_code}"}
            
        data = resp.json()
        urls_data = data.get("urls", [])
        
        async with LocalSession() as session:
            for item in urls_data[:100]:
                raw_url = item.get("url")
                if not raw_url:
                    continue
                    
                threat = item.get("threat") or "malware"
                tags = item.get("tags") or []
                url_status = item.get("url_status") or "online"
                
                existing = (await session.execute(
                    select(ThreatIndicator).where(
                        ThreatIndicator.indicator == raw_url,
                        ThreatIndicator.source == "URLHAUS"
                    )
                )).scalar_one_or_none()
                
                if existing:
                    existing.last_seen = datetime.utcnow()
                    existing.tags = list(set(existing.tags + tags)) if existing.tags else tags
                    existing.status = "ACTIVE" if url_status == "online" else "INACTIVE"
                    updated_count += 1
                else:
                    new_indicator = ThreatIndicator(
                        indicator=raw_url,
                        indicator_type="URL",
                        source="URLHAUS",
                        classification="MALICIOUS",
                        confidence=0.98,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        status="ACTIVE" if url_status == "online" else "INACTIVE",
                        tags=tags,
                        metadata_payload={"threat": threat, "urlhaus_id": item.get("id")}
                    )
                    session.add(new_indicator)
                    new_count += 1
                    
            await session.commit()
            
        return {
            "status": "SUCCESS",
            "source": "URLHAUS",
            "new_count": new_count,
            "updated_count": updated_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}
    finally:
        await local_engine.dispose()
