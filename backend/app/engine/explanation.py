from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.investigation import Investigation
from ..models.finding import Finding
from ..models.agent import Evidence, SandboxSession

class RiskExplanationService:
    @staticmethod
    async def generate_explanation(investigation_id: str, session: AsyncSession) -> dict:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            return {"error": "Investigation not found"}
        
        findings_res = await session.execute(
            select(Finding).where(Finding.investigation_id == investigation_id).order_by(Finding.risk_contribution.desc())
        )
        findings = findings_res.scalars().all()
        
        evidence_res = await session.execute(
            select(Evidence).where(Evidence.investigation_id == investigation_id).order_by(Evidence.created_at.desc())
        )
        evidence = evidence_res.scalars().all()
        
        sb_res = await session.execute(
            select(SandboxSession).where(SandboxSession.investigation_id == investigation_id)
        )
        sandbox = sb_res.scalars().first()
        
        score = inv.final_risk_score or 0.0
        level = inv.classification or "UNKNOWN"
        
        # Build Risk Factors from actual findings
        risk_factors = []
        for f in findings:
            if f.risk_contribution and f.risk_contribution > 0:
                risk_factors.append({
                    "factor": f.title,
                    "description": f.description,
                    "severity": f.severity,
                    "category": f.category,
                    "contribution": f.risk_contribution
                })
                
        # Build Actionable Recommendations
        recommendations = []
        categories = {f.category for f in findings}
        
        if "credential_harvesting" in categories or "email_spoofing" in categories:
            recommendations.append("DO NOT enter login credentials, passwords, or two-factor codes on this page.")
        if "quishing" in categories:
            recommendations.append("Do not scan untrusted QR codes or navigate to destination URLs without verification.")
        if "threat_intel" in categories or score >= 70:
            recommendations.append("Block the indicator immediately across edge firewalls and DNS resolvers.")
            recommendations.append("Sinkhole domain requests and revoke any active user sessions that visited this destination.")
        if "smishing" in categories:
            recommendations.append("Do not reply to the SMS or provide any personal verification numbers (OTP).")
        if "financial_fraud" in categories:
            recommendations.append("Do not transfer funds, authorize wire payments, or purchase gift cards.")
        if "malware_delivery" in categories or (sandbox and sandbox.event_count and sandbox.event_count > 0):
            recommendations.append("Isolate any host that downloaded files from this URL for anti-malware scanning.")
            
        if not recommendations:
            if level in ["SAFE", "LOW"]:
                recommendations.append("No active threat detected. Continue to follow standard security awareness practices.")
            else:
                recommendations.append("Exercise caution and verify the source through an out-of-band communication channel.")
                
        summary = (
            f"Target was classified as {level} risk with a score of {score}/100 based on "
            f"{len(findings)} independent agent observations and threat intelligence correlations."
        )

        return {
            "title": f"{level} RISK ASSESSMENT ({score}/100)",
            "classification": level,
            "score": score,
            "confidence": inv.confidence or 0.95,
            "summary": summary,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "evidence_count": len(evidence),
            "evidence_highlights": [e.observed_fact for e in evidence[:8]],
            "sandbox_confirmed": bool(sandbox and sandbox.status.value == "COMPLETED" and sandbox.event_count and sandbox.event_count > 0)
        }
