from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from ..models.finding import Finding
from ..models.investigation import Investigation

class FindingCorrelationService:
    @staticmethod
    async def correlate(investigation_id: str, session: AsyncSession):
        # Load all current findings for this investigation
        result = await session.execute(
            select(Finding).where(Finding.investigation_id == investigation_id)
        )
        existing_findings: List[Finding] = result.scalars().all()
        
        has_credential_req = any(f.category == "credential_harvesting" for f in existing_findings)
        has_brand_impersonation = any(f.category == "impersonation" for f in existing_findings)
        has_suspicious_url = any(f.category in ["evasion", "suspicious_infrastructure"] for f in existing_findings)
        has_urgency = any(f.category == "social_engineering" for f in existing_findings)
        has_threat_intel = any(f.category == "threat_intel" for f in existing_findings)
        
        findings = []
        
        # URL + Brand = Stronger Phishing Signal
        if has_suspicious_url and has_brand_impersonation:
            findings.append(Finding(
                investigation_id=investigation_id, agent="correlation_engine", category="multi_signal_phishing",
                title="Suspicious URL hosting Brand Impersonation", 
                description="High confidence: Evasion techniques detected on a domain impersonating a brand.",
                severity="critical", confidence=0.98, risk_contribution=45
            ))
            
        # Credential Request + Suspicious URL = Credential Harvesting
        if has_credential_req and has_suspicious_url:
            findings.append(Finding(
                investigation_id=investigation_id, agent="correlation_engine", category="multi_signal_phishing",
                title="Credential Harvesting Infrastructure", 
                description="High confidence: Credential request observed on suspicious infrastructure.",
                severity="critical", confidence=0.95, risk_contribution=40
            ))
            
        # Urgency + Financial Request = Social Engineering Risk
        has_financial = any(f.category == "financial_fraud" for f in existing_findings)
        if has_urgency and has_financial:
            findings.append(Finding(
                investigation_id=investigation_id, agent="correlation_engine", category="scam",
                title="Urgent Financial Scam", 
                description="High confidence: Urgent social engineering combined with financial requests.",
                severity="high", confidence=0.90, risk_contribution=35
            ))

        if findings:
            session.add_all(findings)
            await session.commit()
