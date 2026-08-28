import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from ..models import Investigation, InvestigationStatus, Incident, Evidence
from ..models.autonomous import (
    InvestigationPlan, InvestigationTask, AgentMessage, ResponseAction
)
from .risk import RiskEngine

class InvestigationCoordinator:
    """
    Manages the autonomous loop: OBSERVE -> PLAN -> EXECUTE -> REASSESS -> STOP
    """
    
    MAX_ITERATIONS = 5

    @classmethod
    async def start_investigation(cls, investigation_id: str):
        from ..database.connection import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await cls.run_loop(investigation_id, session)

    @classmethod
    async def run_loop(cls, investigation_id: str, db: AsyncSession):
        from .agent_router import AgentRouter
        from ..worker import celery_app
        
        inv = await db.get(Investigation, investigation_id)
        if not inv or inv.status in [InvestigationStatus.COMPLETED, InvestigationStatus.FAILED]:
            return
            
        inv.status = InvestigationStatus.AGENT_ANALYSIS
        await db.commit()
        
        iteration = 0
        
        while iteration < cls.MAX_ITERATIONS:
            iteration += 1
            print(f"[Coordinator] {investigation_id} | Iteration {iteration}")
            
            # 1. OBSERVE & REASSESS
            risk_output = await RiskEngine.calculate_risk(investigation_id, db)
            inv.final_risk_score = risk_output.score
            inv.classification = risk_output.level
            await db.commit()
            await db.refresh(inv)
            
            # 2. STOP CONDITIONS
            if cls._should_stop(inv):
                break
                
            # 3. PLAN
            plan_result = await cls._generate_plan(inv, db)
            if not plan_result or not plan_result.evidence:
                break
                
            planned_agents = plan_result.evidence[0].get("planned_agents", [])
                
            # 4. EXECUTE
            # We use Celery for async execution of the planned agents
            tasks = []
            for agent_name in planned_agents:
                # Dispatch to celery worker
                res = celery_app.send_task("execute_agent_task", args=[investigation_id, agent_name, {}])
                tasks.append(res)
                
                # Log task in DB
                db_task = InvestigationTask(
                    investigation_id=investigation_id,
                    task_type="AGENT_EXECUTION",
                    assigned_agent=agent_name,
                    status="QUEUED"
                )
                db.add(db_task)
            
            await db.commit()
            
            # Wait for tasks to complete without blocking event loop
            import asyncio
            loop = asyncio.get_running_loop()
            while True:
                all_ready = True
                for t in tasks:
                    is_ready = await loop.run_in_executor(None, t.ready)
                    if not is_ready:
                        all_ready = False
                        break
                if all_ready:
                    break
                await asyncio.sleep(2)
                
            # Mark tasks completed
            for t in tasks:
                pass # In production we would update task DB status here
                
        # STOP: Wrap up the investigation
        inv.status = InvestigationStatus.COMPLETED
        inv.current_stage = "Incident Summarization & Response"
        inv.completed_at = datetime.utcnow()
        await db.commit()
        
        # Trigger Incident creation & Response Action
        await cls._finalize_investigation(investigation_id, db)

    @classmethod
    def _should_stop(cls, inv: Investigation) -> bool:
        if inv.final_risk_score and inv.final_risk_score > 90:
            return True # Sufficiently critical to stop and block immediately
        return False
        
    @classmethod
    async def _generate_plan(cls, inv: Investigation, db: AsyncSession):
        from ..agents.investigation_planner import InvestigationPlannerAgent
        # Simplified plan generation using the existing planner
        return await InvestigationPlannerAgent.analyze(inv.id, db)
        
    @classmethod
    async def _finalize_investigation(cls, investigation_id: str, db: AsyncSession):
        from ..agents.response_agent import ResponseAgent
        # Run response agent
        await ResponseAgent.analyze(investigation_id, db)
        
        # Create Incident if Risk is Medium or higher
        inv = await db.get(Investigation, investigation_id)
        if inv.final_risk_score and inv.final_risk_score > 40:
            incident = Incident(
                investigation_id=investigation_id,
                title=f"Suspicious {inv.input_type.value} Analysis",
                severity=inv.classification,
                priority="HIGH" if inv.final_risk_score > 70 else "MEDIUM",
                summary="Automatically created after autonomous loop.",
                status="INVESTIGATING"
            )
            db.add(incident)
            await db.commit()
