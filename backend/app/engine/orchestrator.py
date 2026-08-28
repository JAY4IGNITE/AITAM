import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database.connection import AsyncSessionLocal
from ..models.investigation import Investigation, InvestigationStatus
from ..models.event import InvestigationEvent
from ..agents.url_agent import URLIntelligenceAgent
from ..agents.nlp_agent import NLPAnalysisAgent
from ..agents.brand_agent import BrandImpersonationAgent
from ..agents.threat_intel import ThreatIntelligenceAgent
from ..agents.qr_agent import QRAgent
from ..engine.risk import RiskEngine

class Orchestrator:
    @staticmethod
    async def log_event(session: AsyncSession, inv_id: str, event_type: str, source: str, metadata: dict = None):
        event = InvestigationEvent(
            investigation_id=inv_id,
            event_type=event_type,
            source=source,
            metadata_payload=metadata or {}
        )
        session.add(event)
        await session.commit()

    @staticmethod
    async def start_investigation(investigation_id: str):
        # We run this in a background task
        async with AsyncSessionLocal() as session:
            inv = await session.get(Investigation, investigation_id)
            if not inv:
                return
            
            try:
                # 1. INITIAL ANALYSIS
                inv.status = InvestigationStatus.INITIAL_ANALYSIS
                inv.current_stage = "Preprocessing Input"
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "INITIAL_ANALYSIS_STARTED", "Orchestrator")
                
                # 2. AGENT ANALYSIS
                inv.status = InvestigationStatus.AGENT_ANALYSIS
                inv.current_stage = "Running AI Agents"
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "AGENT_ANALYSIS_STARTED", "Orchestrator")
                
                # Execute agents concurrently
                await asyncio.gather(
                    URLIntelligenceAgent.analyze(inv.id, session),
                    NLPAnalysisAgent.analyze(inv.id, session),
                    BrandImpersonationAgent.analyze(inv.id, session),
                    ThreatIntelligenceAgent.analyze(inv.id, session),
                    QRAgent.analyze(inv.id, session)
                )
                
                # 3. RISK EVALUATION
                inv.status = InvestigationStatus.RISK_EVALUATION
                inv.current_stage = "Calculating Initial Risk"
                await session.commit()
                
                initial_risk = await RiskEngine.calculate_risk(inv.id, session)
                inv.initial_risk_score = initial_risk
                await Orchestrator.log_event(session, inv.id, "RISK_CALCULATED", "RiskEngine", {"initial_risk": initial_risk})
                
                # 4. DECISION (SANDBOX or PROCEED)
                if initial_risk > 40: # Suspicious or higher
                    inv.status = InvestigationStatus.SANDBOX_QUEUED
                    inv.current_stage = "Queuing for Sandbox"
                    await session.commit()
                    await Orchestrator.log_event(session, inv.id, "SANDBOX_QUEUED", "Orchestrator")
                    
                    inv.status = InvestigationStatus.SANDBOX_RUNNING
                    inv.current_stage = "Isolating in Sandbox"
                    await session.commit()
                    await Orchestrator.log_event(session, inv.id, "SANDBOX_STARTED", "SandboxAgent")
                    
                    # Trigger Sandbox
                    from ..agents.sandbox_agent import SandboxAgent
                    await SandboxAgent.analyze(inv.id, session)
                    
                    inv.status = InvestigationStatus.BEHAVIOR_ANALYSIS
                    inv.current_stage = "Analyzing Browser Behavior"
                    await session.commit()
                    await Orchestrator.log_event(session, inv.id, "BEHAVIOR_ANALYSIS_COMPLETED", "SandboxAgent")
                    
                    # 5. RE_EVALUATION
                    inv.status = InvestigationStatus.RE_EVALUATION
                    inv.current_stage = "Re-evaluating Risk"
                    await session.commit()
                    
                    final_risk = await RiskEngine.calculate_risk(inv.id, session)
                    inv.final_risk_score = final_risk
                    await Orchestrator.log_event(session, inv.id, "RISK_RECALCULATED", "RiskEngine", {"final_risk": final_risk})
                    
                    if final_risk > 80:
                        inv.status = InvestigationStatus.DEEP_ANALYSIS
                        inv.current_stage = "Deep Forensic Analysis"
                        await session.commit()
                        await Orchestrator.log_event(session, inv.id, "DEEP_ANALYSIS_TRIGGERED", "Orchestrator")
                else:
                    inv.final_risk_score = initial_risk
                    
                # 6. EVIDENCE CORRELATION
                inv.status = InvestigationStatus.EVIDENCE_CORRELATION
                inv.current_stage = "Correlating Evidence"
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "EVIDENCE_CORRELATION_STARTED", "Orchestrator")
                
                # 7. REPORT GENERATION
                inv.status = InvestigationStatus.REPORT_GENERATION
                inv.current_stage = "Generating Intelligence Report"
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "REPORT_GENERATED", "Orchestrator")
                
                # FINAL COMPLETED STATE
                inv.status = InvestigationStatus.COMPLETED
                inv.current_stage = "Analysis Complete"
                inv.completed_at = datetime.utcnow()
                
                if inv.final_risk_score > 80:
                    inv.classification = "CRITICAL"
                elif inv.final_risk_score > 60:
                    inv.classification = "HIGH"
                elif inv.final_risk_score > 40:
                    inv.classification = "SUSPICIOUS"
                elif inv.final_risk_score > 20:
                    inv.classification = "LOW"
                else:
                    inv.classification = "SAFE"
                    
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "INVESTIGATION_COMPLETED", "Orchestrator")
                
            except Exception as e:
                inv.status = InvestigationStatus.FAILED
                inv.current_stage = "Error"
                inv.completed_at = datetime.utcnow()
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "INVESTIGATION_FAILED", "Orchestrator", {"error": str(e)})
                print(f"Investigation failed: {e}")
