from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentOutput, Signal
from urllib.parse import urlparse

class BrandImpersonationAgent(BaseAgent):
    agent_name = "brand_impersonation"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        
        if inv.input_type.value not in ["URL", "WEBPAGE"]:
            run.outputs = {"message": "Brand impersonation skipped for non-URL inputs."}
            run.confidence = 1.0
            return
            
        url = inv.target
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # MOCK IMPLEMENTATION
        # In a real system, this would use computer vision on the page screenshot
        # and fuzzy matching against a brand database.
        
        signals = []
        risk_score = 0.0
        
        known_brands = {
            "microsoft": "microsoft.com",
            "paypal": "paypal.com",
            "apple": "apple.com",
            "chase": "chase.com"
        }
        
        claimed_brand = None
        for brand, official_domain in known_brands.items():
            if brand in domain and domain != official_domain and not domain.endswith("." + official_domain):
                claimed_brand = brand
                risk_score = 85.0
                signals.append(Signal(
                    type="brand_impersonation",
                    severity="high",
                    evidence=f"Domain {domain} resembles {brand} but is not the official domain ({official_domain})"
                ))
                break
                
        output = AgentOutput(
            agent_name=cls.agent_name,
            risk_score=risk_score,
            confidence=0.90 if risk_score > 0 else 0.5,
            signals=signals
        )
        
        run.outputs = output.dict()
        run.confidence = output.confidence
        
        for sig in signals:
            ev = Evidence(
                investigation_id=investigation_id,
                agent_name=cls.agent_name,
                evidence_type=sig.type,
                severity=sig.severity,
                observed_fact=sig.evidence,
                confidence=output.confidence
            )
            session.add(ev)
