import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database.connection import AsyncSessionLocal
from ..models.investigation import Investigation, InvestigationStatus
from ..agents.url_agent import URLIntelligenceAgent
from ..agents.nlp_agent import NLPAnalysisAgent
from ..agents.brand_agent import BrandImpersonationAgent
from ..agents.threat_intel import ThreatIntelligenceAgent
from ..agents.qr_agent import QRAgent
from ..engine.risk import RiskEngine

class Orchestrator:
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
                await session.commit()
                
                # Execute agents concurrently
                await asyncio.gather(
                    URLIntelligenceAgent.analyze(inv.id, session),
                    NLPAnalysisAgent.analyze(inv.id, session),
                    BrandImpersonationAgent.analyze(inv.id, session),
                    ThreatIntelligenceAgent.analyze(inv.id, session),
                    QRAgent.analyze(inv.id, session)
                )
                
                # 2. INITIAL RISK SCORE
                inv.status = InvestigationStatus.INITIAL_RISK_EVALUATION
                await session.commit()
                
                initial_risk = await RiskEngine.calculate_risk(inv.id, session)
                inv.initial_risk_score = initial_risk
                
                # 3. DECISION
                if initial_risk > 40: # Suspicious or higher
                    inv.status = InvestigationStatus.SANDBOX_PENDING
                    await session.commit()
                    # Trigger Sandbox
                    # await SandboxAgent.analyze(inv.id, session)
                
                # ... other states ...
                
                # FINAL REPORT
                inv.status = InvestigationStatus.COMPLETED
                inv.final_risk_score = initial_risk # mock for now
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
                
            except Exception as e:
                inv.status = InvestigationStatus.FAILED
                await session.commit()
                print(f"Investigation failed: {e}")

