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

class SocialMessageIntelligenceAgent(BaseAgent):
    agent_name = "social_intelligence"
    agent_version = "2.0.0"
    capabilities = [
        "crypto_giveaway_scams", "fake_support_detection", "account_recovery_fraud",
        "investment_fraud", "url_extraction", "social_engineering"
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
            evidence_items.append({"type": "SOCIAL_URL", "fact": f"Extracted {len(extracted_urls)} URL(s) from social message"})
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

        # 2. Crypto & Giveaway Fraud
        crypto_keywords = [
            "giveaway", "send 1 btc get 2", "eth airdrop", "free crypto", "elon musk", "binance airdrop",
            "crypto doubler", "connect wallet", "claim airdrop", "seed phrase", "private key"
        ]
        if any(kw in text_lower for kw in crypto_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="social_scam",
                title="Cryptocurrency / Airdrop Giveaway Scam",
                description="The social message promises fraudulent crypto multipliers, airdrops, or requests wallet connection.",
                severity="critical",
                confidence=0.96,
                risk_contribution=45
            ))
            evidence_items.append({"type": "CRYPTO_SCAM", "fact": "Cryptocurrency giveaway or wallet draining pattern detected"})

        # 3. Fake Customer Support & Helpdesk Impersonation
        support_keywords = [
            "official support", "helpdesk team", "send dm to recover", "dm support", "ticket resolved",
            "contact our agent on telegram", "whatsapp support", "meta support team", "instagram copyright team"
        ]
        if any(kw in text_lower for kw in support_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="impersonation",
                title="Fake Customer Support Impersonation",
                description="Message impersonates platform helpdesk or instructs the victim to message third-party channels (Telegram/WhatsApp).",
                severity="high",
                confidence=0.92,
                risk_contribution=35
            ))
            evidence_items.append({"type": "FAKE_SUPPORT", "fact": "Fake support or off-platform redirection detected"})

        # 4. Account Recovery & Shadowban Scam
        recovery_keywords = [
            "violated community guidelines", "copyright infringement", "account disabled in 24 hours",
            "appeal copyright", "appeal violation", "unban your account", "recover banned account"
        ]
        if any(kw in text_lower for kw in recovery_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="social_engineering",
                title="Account Suspension / Copyright Appeal Lure",
                description="Message threatens immediate account deletion or copyright sanctions to panic the victim into entering credentials.",
                severity="high",
                confidence=0.90,
                risk_contribution=35
            ))
            evidence_items.append({"type": "COPYRIGHT_LURE", "fact": "Fake copyright / policy violation threat detected"})

        # 5. Guaranteed Investment & High Yield Scams
        invest_keywords = ["guaranteed return", "daily profit", "passive income 100%", "investment mentor", "trading signal", "forex robot"]
        if any(kw in text_lower for kw in invest_keywords):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="financial_fraud",
                title="High-Yield Investment Fraud (HYIP)",
                description="Message advertises unrealistic guaranteed returns or unregulated trading schemes.",
                severity="high",
                confidence=0.88,
                risk_contribution=30
            ))
            evidence_items.append({"type": "INVESTMENT_SCAM", "fact": "Unrealistic high-yield investment lure detected"})

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
                "is_crypto_scam": any(kw in text_lower for kw in crypto_keywords),
                "is_support_scam": any(kw in text_lower for kw in support_keywords)
            }
        )
