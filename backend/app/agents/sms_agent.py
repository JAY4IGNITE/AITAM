import re
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.iocs import IOC

URL_REGEX = re.compile(r'https?://(?:[a-zA-Z0-9-._~:/?#\[\]@!$&\'()*+,;=]|%[0-9a-fA-F]{2})+')

class SMSIntelligenceAgent(BaseAgent):
    agent_name = "sms_intelligence"
    agent_version = "2.0.0"
    capabilities = [
        "smishing_detection", "otp_fraud_detection", "package_delivery_scams",
        "bank_impersonation", "url_extraction", "urgency_analysis"
    ]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")

        content = inv.normalized_input or inv.target
        text_lower = content.lower()
        findings: list[Finding] = []
        evidence_items: list[dict] = []

        # 1. URL Extraction
        found_urls = URL_REGEX.findall(content)
        extracted_urls = list(dict.fromkeys(found_urls))

        if extracted_urls:
            evidence_items.append({"type": "SMS_URL", "fact": f"Extracted {len(extracted_urls)} embedded link(s) from SMS"})
            for u in extracted_urls:
                session.add(IOC(
                    investigation_id=investigation_id,
                    ioc_type="URL",
                    value=u,
                    source_agent=cls.agent_name,
                    confidence=0.95,
                    first_seen=datetime.utcnow().isoformat(),
                    last_seen=datetime.utcnow().isoformat()
                ))

        # 2. OTP / 2FA Theft Smishing
        otp_keywords = ["otp", "verification code", "one-time passcode", "2fa code", "do not share", "security code", "auth code"]
        if any(kw in text_lower for kw in otp_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="credential_harvesting",
                title="OTP / 2FA Theft Lure Detected",
                description="Message requests or references one-time verification codes, characteristic of MFA bypass attacks.",
                severity="critical",
                confidence=0.95,
                risk_contribution=45
            ))
            evidence_items.append({"type": "OTP_LURE", "fact": "OTP / Security verification code keywords detected in SMS"})

        # 3. Bank / Financial Impersonation Smishing
        bank_keywords = ["chase", "wells fargo", "bank of america", "citi", "paypal", "venmo", "zelle", "fraud alert", "debit card blocked", "unauthorized transaction", "card suspended"]
        if any(kw in text_lower for kw in bank_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="impersonation",
                title="Financial Institution Smishing Impersonation",
                description="The SMS pretends to be a fraud alert or status warning from a major bank or payment provider.",
                severity="critical",
                confidence=0.92,
                risk_contribution=40
            ))
            evidence_items.append({"type": "BANK_IMPERSONATION", "fact": "Bank or payment service impersonation detected in SMS"})

        # 4. Package Delivery & Parcel Scams
        delivery_keywords = ["usps", "fedex", "ups", "dhl", "package delivery", "parcel pending", "customs fee", "unpaid postage", "reschedule delivery", "address verification"]
        if any(kw in text_lower for kw in delivery_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="smishing",
                title="Package Delivery Scam Detected",
                description="SMS uses fake parcel tracking or unpaid postage lures to trick recipients into entering payment information.",
                severity="high",
                confidence=0.90,
                risk_contribution=35
            ))
            evidence_items.append({"type": "DELIVERY_SCAM", "fact": "Package delivery tracking / fee payment lure detected"})

        # 5. Account Suspension & High Urgency Lures
        suspension_keywords = ["account suspended", "locked out", "act immediately", "within 15 minutes", "within 1 hour", "service disconnected", "urgent update required"]
        if any(kw in text_lower for kw in suspension_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="social_engineering",
                title="Urgent Account Suspension Threat",
                description="High-urgency language threatening immediate account termination or lockouts.",
                severity="high",
                confidence=0.88,
                risk_contribution=30
            ))
            evidence_items.append({"type": "URGENCY", "fact": "Immediate suspension threat detected in SMS"})

        # 6. Prize / Lottery / Gift Card Scams
        prize_keywords = ["congratulations you won", "claim your prize", "free gift card", "selected for $", "claim reward", "lottery winner"]
        if any(kw in text_lower for kw in prize_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="social_engineering",
                title="Lottery / Prize Scam Lure",
                description="The SMS advertises fraudulent lottery winnings or unsolicited gift rewards.",
                severity="high",
                confidence=0.90,
                risk_contribution=30
            ))
            evidence_items.append({"type": "PRIZE_SCAM", "fact": "Prize or lottery scam lure detected"})

        # Persist findings & evidence
        if findings:
            session.add_all(findings)
            for ev in evidence_items:
                session.add(Evidence(
                    investigation_id=investigation_id,
                    agent_name=cls.agent_name,
                    evidence_type=ev["type"],
                    severity="high" if any(f.severity in ["critical", "high"] for f in findings) else "medium",
                    observed_fact=ev["fact"],
                    confidence=0.95
                ))

        return AgentResult(
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="COMPLETED",
            execution_time=0.0,
            findings=[{"title": f.title, "severity": f.severity, "category": f.category} for f in findings],
            evidence=evidence_items,
            confidence=0.95,
            metadata={
                "extracted_urls": extracted_urls,
                "has_otp_lure": any(kw in text_lower for kw in otp_keywords),
                "has_bank_lure": any(kw in text_lower for kw in bank_keywords)
            }
        )
