import os
import asyncio
from celery import Celery
from .database.connection import AsyncSessionLocal

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("threatlens_backend", broker=redis_url, backend=redis_url)

@celery_app.task(name="execute_agent_task", bind=True, max_retries=3)
def execute_agent_task(self, investigation_id: str, agent_name: str, payload: dict):
    # Start asyncio event loop to run the async agent
    return asyncio.run(_run_agent(investigation_id, agent_name, payload))

async def _run_agent(investigation_id: str, agent_name: str, payload: dict):
    import sys
    from .agents.base import BaseAgent
    # Ensure all agents are loaded
    from .agents import url_agent, content_agent, brand_agent, threat_intel, phishing_agent, email_agent, sms_agent, social_agent, triage_agent, investigation_planner, response_agent, incident_summarization
    
    agent_classes = {cls.__name__: cls for cls in BaseAgent.__subclasses__()}
    if agent_name not in agent_classes:
        return {"status": "FAILED", "error": f"Agent {agent_name} not found"}
        
    agent_class = agent_classes[agent_name]
    
    import os
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/threatlens")
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
    # Using asyncpg requires a separate engine per event loop when in threads
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
