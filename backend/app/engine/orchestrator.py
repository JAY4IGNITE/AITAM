import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database.connection import AsyncSessionLocal
from ..models.investigation import Investigation, InvestigationStatus
from ..models.event import InvestigationEvent
from ..models.autonomous import TriageResult, InvestigationPlan
from ..engine.agent_router import AgentRouter
from ..engine.correlation import FindingCorrelationService
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
                
                from ..engine.input_processor import UniversalInputProcessor
                threat_object = UniversalInputProcessor.process_input(inv.input_type, inv.target)
                inv.normalized_input = threat_object.normalized_text
                await session.commit()
                
                from ..models.journey import RiskAssessment
                init_risk = await RiskEngine.calculate_risk(inv.id, session)
                session.add(RiskAssessment(
                    investigation_id=inv.id, stage="INITIAL", score=init_risk.score,
                    level=init_risk.level, reasons=[{"finding": r.finding, "contribution": r.contribution} for r in init_risk.reasons]
                ))
                await session.commit()
                
                # 2. AUTONOMOUS TRIAGE
                inv.current_stage = "Autonomous Triage"
                await session.commit()
                
                from ..agents.triage_agent import TriageAgent
                await TriageAgent.analyze(inv.id, session)
                
                # Get Triage Result
                triage = (await session.execute(select(TriageResult).where(TriageResult.investigation_id == inv.id))).scalar_one_or_none()
                is_high_priority = triage and triage.priority == "HIGH"
                
                if is_high_priority:
                    # 3. INVESTIGATION PLANNER
                    inv.current_stage = "Investigation Planning"
                    await session.commit()
                    
                    from ..agents.investigation_planner import InvestigationPlannerAgent
                    await InvestigationPlannerAgent.analyze(inv.id, session)
                    
                    plan = (await session.execute(select(InvestigationPlan).where(InvestigationPlan.investigation_id == inv.id))).scalar_one_or_none()
                    
                    inv.status = InvestigationStatus.AGENT_ANALYSIS
                    inv.current_stage = "Running AI Agents"
                    await session.commit()
                    await Orchestrator.log_event(session, inv.id, "AGENT_ANALYSIS_STARTED", "Orchestrator")
                    
                    # Dynamically map strings to Agent Classes
                    import sys
                    from importlib import import_module
                    # Instead of complex reflection, we can fetch all subclasses of BaseAgent
                    from ..agents.base import BaseAgent
                    # Ensure modules are loaded
                    from ..agents.url_agent import URLIntelligenceAgent
                    from ..agents.content_agent import ContentIntelligenceAgent
                    from ..agents.brand_agent import BrandImpersonationAgent
                    from ..agents.threat_intel import ThreatIntelligenceAgent
                    from ..agents.phishing_agent import PhishingDetectionAgent
                    from ..agents.email_agent import EmailIntelligenceAgent
                    from ..agents.sms_agent import SMSIntelligenceAgent
                    from ..agents.social_agent import SocialMessageIntelligenceAgent
                    
                    agent_classes = {cls.__name__: cls for cls in BaseAgent.__subclasses__()}
                    
                    agents_to_run = []
                    if plan and plan.planned_agents:
                        for a_name in plan.planned_agents:
                            if a_name in agent_classes:
                                agents_to_run.append(agent_classes[a_name])
                    
                    if not agents_to_run: # Fallback
                        agents_to_run = AgentRouter.get_route(inv.input_type)
                        
                    async def run_agent(agent_class, i_id):
                        async with AsyncSessionLocal() as agent_session:
                            return await agent_class.analyze(i_id, agent_session)
                            
                    if agents_to_run:
                        await asyncio.gather(*[run_agent(ac, inv.id) for ac in agents_to_run])
                        
                else:
                    await Orchestrator.log_event(session, inv.id, "TRIAGE_SKIPPED_AGENTS", "Orchestrator", {"reason": triage.reason if triage else "LOW PRIORITY"})
                    
                # 4. EVIDENCE CORRELATION
                inv.status = InvestigationStatus.EVIDENCE_CORRELATION
                inv.current_stage = "Correlating Evidence"
                await session.commit()
                
                async with AsyncSessionLocal() as corr_session:
                    await FindingCorrelationService.correlate(inv.id, corr_session)
                
                # 5. RISK EVALUATION
                inv.status = InvestigationStatus.RISK_EVALUATION
                inv.current_stage = "Calculating Risk"
                await session.commit()
                
                risk_output = await RiskEngine.calculate_risk(inv.id, session)
                inv.initial_risk_score = risk_output.score
                await Orchestrator.log_event(session, inv.id, "RISK_CALCULATED", "RiskEngine", {"initial_risk": risk_output.score})
                
                session.add(RiskAssessment(
                    investigation_id=inv.id, stage="AGENTS", score=risk_output.score,
                    level=risk_output.level, reasons=[{"finding": r.finding, "contribution": r.contribution} for r in risk_output.reasons]
                ))
                await session.commit()
                
                # 6. DECISION (SANDBOX or PROCEED) - ONLY if HIGH PRIORITY
                if is_high_priority and risk_output.sandbox_required: 
                    inv.status = InvestigationStatus.SANDBOX_QUEUED
                    inv.current_stage = "Queuing for Sandbox"
                    await session.commit()
                    
                    inv.status = InvestigationStatus.SANDBOX_RUNNING
                    inv.current_stage = "Isolating in Sandbox"
                    await session.commit()
                    await Orchestrator.log_event(session, inv.id, "SANDBOX_STARTED", "SandboxAgent")
                    
                    from ..agents.sandbox_agent import SandboxAgent
                    await SandboxAgent.analyze(inv.id, session)
                    
                    sb_risk = await RiskEngine.calculate_risk(inv.id, session)
                    session.add(RiskAssessment(
                        investigation_id=inv.id, stage="SANDBOX", score=sb_risk.score,
                        level=sb_risk.level, reasons=[{"finding": r.finding, "contribution": r.contribution} for r in sb_risk.reasons]
                    ))
                    await session.commit()
                    
                    inv.status = InvestigationStatus.BEHAVIOR_ANALYSIS
                    inv.current_stage = "Analyzing Browser Behavior"
                    await session.commit()
                    
                    from ..agents.behavior_agent import BehaviorAnalysisAgent
                    await BehaviorAnalysisAgent.analyze(inv.id, session)
                    
                    inv.status = InvestigationStatus.RE_EVALUATION
                    inv.current_stage = "Re-evaluating Risk"
                    await session.commit()
                    
                    final_risk_output = await RiskEngine.calculate_risk(inv.id, session)
                    inv.final_risk_score = final_risk_output.score
                    
                    from ..engine.escalation import EscalationEngine
                    await EscalationEngine.evaluate_and_escalate(inv.id, session)
                    
                    if final_risk_output.deep_analysis_required:
                        inv.status = InvestigationStatus.DEEP_ANALYSIS
                        inv.current_stage = "Deep Forensic Analysis"
                        await session.commit()
                        await Orchestrator.log_event(session, inv.id, "DEEP_ANALYSIS_TRIGGERED", "Orchestrator")
                else:
                    inv.final_risk_score = risk_output.score
                    final_risk_output = risk_output
                    
                # Store Final Risk Assessment
                session.add(RiskAssessment(
                    investigation_id=inv.id, stage="FINAL", score=final_risk_output.score,
                    level=final_risk_output.level, reasons=[{"finding": r.finding, "contribution": r.contribution} for r in final_risk_output.reasons]
                ))
                await session.commit()
                
                # 7. RESPONSE AGENT
                inv.current_stage = "Automated Mitigation Response"
                await session.commit()
                
                from ..agents.response_agent import ResponseAgent
                await ResponseAgent.analyze(inv.id, session)
                
                # 8. GRAPHS AND REPORTS
                from ..engine.graph_builder import EvidenceGraphService
                from ..engine.journey_builder import AttackJourneyService
                await EvidenceGraphService.build_graph(inv.id, session)
                await AttackJourneyService.build_journey(inv.id, session)
                
                inv.status = InvestigationStatus.REPORT_GENERATION
                inv.current_stage = "Generating Intelligence Report"
                await session.commit()
                
                # FINAL COMPLETED STATE
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
                    
                inv.status = InvestigationStatus.COMPLETED
                inv.current_stage = "Analysis Complete"
                inv.completed_at = datetime.utcnow()
                await session.commit()
                
                await Orchestrator.log_event(session, inv.id, "COMPLETED", "Orchestrator")
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                inv.status = InvestigationStatus.FAILED
                inv.current_stage = "Error"
                inv.completed_at = datetime.utcnow()
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "INVESTIGATION_FAILED", "Orchestrator", {"error": str(e)})
                print(f"Investigation failed: {e}")
