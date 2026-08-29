import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database.connection import AsyncSessionLocal
from ..models.investigation import Investigation, InvestigationStatus, InputType
from ..models.event import InvestigationEvent
from ..models.autonomous import TriageResult, InvestigationPlan, Incident
from ..models.journey import RiskAssessment
from ..models.iocs import IOC
from ..engine.agent_router import AgentRouter
from ..engine.correlation import FindingCorrelationService
from ..engine.risk import RiskEngine
from ..engine.input_processor import UniversalInputProcessor

class Orchestrator:
    @staticmethod
    async def log_event(session: AsyncSession, inv_id: str, event_type: str, source: str, severity: str = "INFO", metadata: dict = None):
        event = InvestigationEvent(
            investigation_id=inv_id,
            event_type=event_type,
            source=source,
            severity=severity,
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
                # 1. INITIAL ANALYSIS & PREPROCESSING
                inv.status = InvestigationStatus.INITIAL_ANALYSIS
                inv.current_stage = "Preprocessing Universal Input"
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "INITIAL_ANALYSIS_STARTED", "Orchestrator", "INFO", {
                    "input_type": inv.input_type.value,
                    "target_preview": inv.target[:100]
                })
                
                threat_object = UniversalInputProcessor.process_input(inv.input_type, inv.target)
                inv.normalized_input = threat_object.normalized_text
                
                for ind in threat_object.extracted_indicators:
                    session.add(IOC(
                        investigation_id=inv.id,
                        ioc_type=ind.type,
                        value=ind.value,
                        source_agent="UniversalInputProcessor",
                        confidence=0.95
                    ))
                await session.commit()
                
                from ..engine.event_broadcaster import event_broadcaster
                from ..schemas.agent_event import AgentEvent
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="orchestrator",
                    agent_name="SOC Orchestrator",
                    event_type="agent_started",
                    status="RUNNING",
                    message=f"Initialized autonomous investigation on target: {inv.target}",
                    data={"input_type": inv.input_type.value, "target": inv.target, "extracted_iocs_count": len(threat_object.extracted_indicators)}
                ))
                
                # 2. AUTONOMOUS TRIAGE AGENT
                inv.current_stage = "Autonomous Triage & Priority Assessment"
                await session.commit()
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="orchestrator",
                    agent_name="SOC Orchestrator",
                    event_type="agent_message",
                    status="RUNNING",
                    message="Passing normalized input artifact to Triage Agent...",
                    data={"sender": "orchestrator", "recipient": "triage_agent"}
                ))
                
                from ..agents.triage_agent import TriageAgent
                await TriageAgent.analyze(inv.id, session)
                
                triage_res = await session.execute(select(TriageResult).where(TriageResult.investigation_id == inv.id))
                triage = triage_res.scalar_one_or_none()
                priority = triage.priority if triage else "P2_HIGH"
                
                # 3. INVESTIGATION PLANNER AGENT
                inv.current_stage = "Planning Agent Execution Pipeline"
                await session.commit()
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="triage_agent",
                    agent_name="Triage Agent",
                    event_type="agent_message",
                    status="RUNNING",
                    message=f"Triage assigned priority {priority}. Handing off to Investigation Planner...",
                    data={"sender": "triage_agent", "recipient": "investigation_planner", "priority": priority}
                ))
                
                from ..agents.investigation_planner import InvestigationPlannerAgent
                await InvestigationPlannerAgent.analyze(inv.id, session)
                
                plan_res = await session.execute(select(InvestigationPlan).where(InvestigationPlan.investigation_id == inv.id))
                plan = plan_res.scalar_one_or_none()
                
                # 4. MULTI-AGENT EXECUTION (URL, Email, SMS, Social, QR, Brand, Content)
                inv.status = InvestigationStatus.AGENT_ANALYSIS
                inv.current_stage = "Executing Specialized Intelligence Agents"
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "AGENT_ANALYSIS_STARTED", "Orchestrator", "INFO", {
                    "priority": priority
                })
                
                # Get agent route based on input type
                agents_to_run = AgentRouter.get_route(inv.input_type)
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="investigation_planner",
                    agent_name="Investigation Planner",
                    event_type="agent_message",
                    status="RUNNING",
                    message=f"Dispatched {len(agents_to_run)} specialized agents in parallel: {', '.join([ac.agent_name for ac in agents_to_run])}",
                    data={"sender": "investigation_planner", "recipient": [ac.agent_name for ac in agents_to_run]}
                ))
                
                async def run_agent(agent_class, i_id):
                    async with AsyncSessionLocal() as agent_session:
                        try:
                            return await agent_class.analyze(i_id, agent_session)
                        except Exception as ex:
                            print(f"[Orchestrator] Agent {agent_class.__name__} error: {ex}")
                            return None
                            
                if agents_to_run:
                    await asyncio.gather(*[run_agent(ac, inv.id) for ac in agents_to_run])
                    
                # 5. EVIDENCE CORRELATION & MULTI-SIGNAL FUSION
                inv.status = InvestigationStatus.EVIDENCE_CORRELATION
                inv.current_stage = "Fusing Cross-Agent Signals & IoCs"
                await session.commit()
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="evidence_fusion",
                    agent_name="Evidence Fusion Agent",
                    event_type="agent_started",
                    status="RUNNING",
                    message="Aggregating and fusing multi-agent telemetry, indicators, and threat intelligence...",
                    data={"stage": "evidence_fusion"}
                ))
                
                async with AsyncSessionLocal() as corr_session:
                    await FindingCorrelationService.correlate(inv.id, corr_session)
                
                # 6. RISK EVALUATION (INITIAL AGENT-BASED SCORE)
                inv.status = InvestigationStatus.RISK_EVALUATION
                inv.current_stage = "Calculating Risk Score & Factors"
                await session.commit()
                
                risk_output = await RiskEngine.calculate_risk(inv.id, session)
                inv.initial_risk_score = risk_output.score
                inv.confidence = 0.95
                await session.commit()
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="risk_agent",
                    agent_name="Risk Evaluation Agent",
                    event_type="risk_updated",
                    status="RUNNING",
                    message=f"Agent-layer risk score: {risk_output.score}/100 ({risk_output.level}) with {len(risk_output.reasons)} active risk factors.",
                    data={
                        "score": risk_output.score,
                        "level": risk_output.level,
                        "sandbox_required": risk_output.sandbox_required,
                        "reasons": [{"finding": r.finding, "contribution": r.contribution} for r in risk_output.reasons]
                    }
                ))
                
                session.add(RiskAssessment(
                    investigation_id=inv.id,
                    stage="AGENTS",
                    score=risk_output.score,
                    level=risk_output.level,
                    reasons=[{"finding": r.finding, "contribution": r.contribution} for r in risk_output.reasons]
                ))
                await session.commit()
                
                # 7. ADAPTIVE SANDBOX DECISION (Detonate if URL/Webpage and risk score/heuristics warrant it)
                has_url_target = inv.input_type in [InputType.URL, InputType.WEBPAGE, InputType.QR] or bool(threat_object.urls)
                should_sandbox = risk_output.sandbox_required and has_url_target
                
                if should_sandbox:
                    inv.status = InvestigationStatus.SANDBOX_QUEUED
                    inv.current_stage = "Queueing for Adaptive Sandbox Detonation"
                    await session.commit()
                    
                    await event_broadcaster.emit(AgentEvent(
                        investigation_id=inv.id,
                        agent_id="sandbox_agent",
                        agent_name="Playwright Sandbox Agent",
                        event_type="agent_started",
                        status="RUNNING",
                        message="Triggered isolated zero-trust browser sandbox for dynamic URL detonation.",
                        data={"target_urls": threat_object.urls or [inv.target]}
                    ))
                    
                    inv.status = InvestigationStatus.SANDBOX_RUNNING
                    inv.current_stage = "Detonating URL in Isolated Sandbox"
                    await session.commit()
                    await Orchestrator.log_event(session, inv.id, "SANDBOX_STARTED", "SandboxAgent", "WARNING")
                    
                    from ..agents.sandbox_agent import SandboxAgent
                    try:
                        await SandboxAgent.analyze(inv.id, session)
                    except Exception as sbe:
                        print(f"[Orchestrator] Sandbox execution notice: {sbe}")
                    
                    inv.status = InvestigationStatus.BEHAVIOR_ANALYSIS
                    inv.current_stage = "Analyzing Browser Behavioral Telemetry"
                    await session.commit()
                    
                    from ..agents.behavior_agent import BehaviorAnalysisAgent
                    await BehaviorAnalysisAgent.analyze(inv.id, session)
                    
                    # Re-correlate with sandbox evidence
                    async with AsyncSessionLocal() as sb_corr_session:
                        await FindingCorrelationService.correlate(inv.id, sb_corr_session)
                        
                    inv.status = InvestigationStatus.RE_EVALUATION
                    inv.current_stage = "Re-evaluating Risk with Behavioral Evidence"
                    await session.commit()
                    
                    final_risk_output = await RiskEngine.calculate_risk(inv.id, session)
                    inv.final_risk_score = final_risk_output.score
                    inv.classification = final_risk_output.level
                    
                    await event_broadcaster.emit(AgentEvent(
                        investigation_id=inv.id,
                        agent_id="risk_agent",
                        agent_name="Risk Evaluation Agent",
                        event_type="risk_updated",
                        status="RUNNING",
                        message=f"Post-detonation risk score recomputed: {final_risk_output.score}/100 ({final_risk_output.level}).",
                        data={
                            "score": final_risk_output.score,
                            "level": final_risk_output.level,
                            "reasons": [{"finding": r.finding, "contribution": r.contribution} for r in final_risk_output.reasons]
                        }
                    ))
                    
                    session.add(RiskAssessment(
                        investigation_id=inv.id,
                        stage="SANDBOX",
                        score=final_risk_output.score,
                        level=final_risk_output.level,
                        reasons=[{"finding": r.finding, "contribution": r.contribution} for r in final_risk_output.reasons]
                    ))
                    await session.commit()
                else:
                    inv.final_risk_score = risk_output.score
                    inv.classification = risk_output.level
                    final_risk_output = risk_output

                # Store Final Risk Assessment
                session.add(RiskAssessment(
                    investigation_id=inv.id,
                    stage="FINAL",
                    score=final_risk_output.score,
                    level=final_risk_output.level,
                    reasons=[{"finding": r.finding, "contribution": r.contribution} for r in final_risk_output.reasons]
                ))
                await session.commit()

                # 8. RESPONSE AGENT
                inv.current_stage = "Formulating Response Actions & Recommendations"
                await session.commit()
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="risk_agent",
                    agent_name="Risk Evaluation Agent",
                    event_type="agent_message",
                    status="RUNNING",
                    message=f"Risk rating: {inv.classification} ({inv.final_risk_score}/100). Passing to SOC Response Agent for playbook formulation...",
                    data={"sender": "risk_agent", "recipient": "response_agent", "classification": inv.classification}
                ))
                
                from ..agents.response_agent import ResponseAgent
                await ResponseAgent.analyze(inv.id, session)
                
                # 9. EVIDENCE GRAPH & ATTACK JOURNEY
                from ..engine.graph_builder import EvidenceGraphService
                from ..engine.journey_builder import AttackJourneyService
                await EvidenceGraphService.build_graph(inv.id, session)
                await AttackJourneyService.build_journey(inv.id, session)
                
                # 10. GENERATE REPORT & INCIDENT IF HIGH RISK
                inv.status = InvestigationStatus.REPORT_GENERATION
                inv.current_stage = "Generating Threat Intelligence Report"
                await session.commit()
                
                from ..engine.report_generator import ReportGenerator
                await ReportGenerator.generate_report(inv.id, session)
                
                await event_broadcaster.emit(AgentEvent(
                    investigation_id=inv.id,
                    agent_id="report_agent",
                    agent_name="Forensic Report Agent",
                    event_type="investigation_completed",
                    status="COMPLETED",
                    message=f"Investigation concluded. Final classification: {inv.classification} ({inv.final_risk_score}/100). Forensic dossier generated.",
                    data={
                        "risk_score": inv.final_risk_score,
                        "classification": inv.classification,
                        "report_id": f"REP-{inv.display_id}",
                        "findings_count": len(final_risk_output.reasons)
                    }
                ))
                
                # Automatically create Incident if Risk is Medium, High, or Critical
                if inv.final_risk_score and inv.final_risk_score >= 40:
                    existing_inc = (await session.execute(select(Incident).where(Incident.investigation_id == inv.id))).scalar_one_or_none()
                    if not existing_inc:
                        incident = Incident(
                            investigation_id=inv.id,
                            title=f"Suspicious {inv.input_type.value} Phishing Alert ({inv.classification})",
                            severity=inv.classification,
                            priority="HIGH" if inv.final_risk_score >= 60 else "MEDIUM",
                            summary=f"Automated multi-agent investigation identified {inv.classification} risk threat with score {inv.final_risk_score}/100.",
                            status="INVESTIGATING"
                        )
                        session.add(incident)
                        await session.commit()
                
                # FINAL COMPLETED STATE
                inv.status = InvestigationStatus.COMPLETED
                inv.current_stage = "Investigation Complete"
                inv.completed_at = datetime.utcnow()
                await session.commit()
                
                await Orchestrator.log_event(session, inv.id, "COMPLETED", "Orchestrator", "INFO", {
                    "final_score": inv.final_risk_score,
                    "classification": inv.classification
                })
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                inv.status = InvestigationStatus.FAILED
                inv.current_stage = f"Failed: {str(e)[:100]}"
                inv.completed_at = datetime.utcnow()
                await session.commit()
                await Orchestrator.log_event(session, inv.id, "INVESTIGATION_FAILED", "Orchestrator", "ERROR", {"error": str(e)})
                print(f"[Orchestrator] Investigation {investigation_id} failed: {e}")
