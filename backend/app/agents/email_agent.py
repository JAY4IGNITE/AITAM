import re
import email
from email import policy
from email.parser import BytesParser, Parser
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse

from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.iocs import IOC
from datetime import datetime

URL_REGEX = re.compile(r'https?://(?:[a-zA-Z0-9-._~:/?#\[\]@!$&\'()*+,;=]|%[0-9a-fA-F]{2})+')

class EmailIntelligenceAgent(BaseAgent):
    agent_name = "email_intelligence"
    agent_version = "2.0.0"
    capabilities = ["header_analysis", "spf_dkim_check", "impersonation_detection", "url_extraction", "lure_analysis"]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")

        content = inv.normalized_input or inv.target
        findings: list[Finding] = []
        evidence_items: list[dict] = []
        extracted_urls: list[str] = []

        # 1. Parse Email Structure (Supports raw RFC822 / MIME or plain text)
        parsed_email = None
        sender = ""
        reply_to = ""
        subject = ""
        body_text = content

        try:
            if "From:" in content or "Subject:" in content:
                parsed_email = Parser(policy=policy.default).parsestr(content)
                sender = parsed_email.get("From", "")
                reply_to = parsed_email.get("Reply-To", "")
                subject = parsed_email.get("Subject", "")
                
                # Extract text body
                if parsed_email.is_multipart():
                    parts = []
                    for part in parsed_email.walk():
                        if part.get_content_type() == "text/plain":
                            parts.append(part.get_content())
                    if parts:
                        body_text = "\n".join(parts)
                else:
                    body_text = parsed_email.get_content() if hasattr(parsed_email, 'get_content') else parsed_email.get_payload()
        except Exception:
            pass

        full_text = f"{subject}\n{body_text}".lower()

        # 2. Extract Embedded URLs
        found_urls = URL_REGEX.findall(content)
        extracted_urls = list(dict.fromkeys(found_urls))

        if extracted_urls:
            evidence_items.append({"type": "EXTRACTED_URLS", "fact": f"Extracted {len(extracted_urls)} embedded URLs from email content"})
            # Save IOCs
            for u in extracted_urls[:10]:
                session.add(IOC(
                    investigation_id=investigation_id,
                    ioc_type="URL",
                    value=u,
                    source_agent=cls.agent_name,
                    confidence=0.95,
                    first_seen=datetime.utcnow().isoformat(),
                    last_seen=datetime.utcnow().isoformat()
                ))

        # 3. Header Analysis: Reply-To vs From Spoofing
        if sender and reply_to and sender.lower() != reply_to.lower():
            # Check domain mismatch
            sender_domain = sender.split("@")[-1].strip(">").lower() if "@" in sender else ""
            reply_domain = reply_to.split("@")[-1].strip(">").lower() if "@" in reply_to else ""
            if sender_domain != reply_domain:
                findings.append(Finding(
                    investigation_id=investigation_id,
                    agent=cls.agent_name,
                    category="email_spoofing",
                    title="Reply-To Domain Mismatch Detected",
                    description=f"Email claims to be from '{sender}', but replies are routed to '{reply_to}', a common spoofing technique.",
                    severity="critical",
                    confidence=0.95,
                    risk_contribution=45
                ))
                evidence_items.append({"type": "HEADER_MISMATCH", "fact": f"Sender '{sender}' mismatches Reply-To '{reply_to}'"})

        # 4. Authentication Headers Check (SPF / DKIM / DMARC Failures)
        if "spf=fail" in content.lower() or "spf: fail" in content.lower() or "spf=softfail" in content.lower():
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="email_spoofing",
                title="SPF Authentication Failed",
                description="Sender Policy Framework (SPF) check failed, indicating the sending server is not authorized for this domain.",
                severity="high",
                confidence=0.92,
                risk_contribution=35
            ))
            evidence_items.append({"type": "AUTH_FAILURE", "fact": "SPF verification failed in email headers"})

        if "dkim=fail" in content.lower() or "dkim: fail" in content.lower():
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="email_spoofing",
                title="DKIM Signature Verification Failed",
                description="DomainKeys Identified Mail (DKIM) cryptographic signature check failed.",
                severity="high",
                confidence=0.92,
                risk_contribution=35
            ))
            evidence_items.append({"type": "AUTH_FAILURE", "fact": "DKIM cryptographic signature verification failed"})

        # 5. Social Engineering & Urgency Analysis
        urgency_patterns = ["immediate action required", "account suspended", "24 hours", "unauthorized access", "terminate your account", "password expired", "security alert"]
        if any(p in full_text for p in urgency_patterns):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="social_engineering",
                title="Urgent Psychological Pressure Detected",
                description="The email leverages high-pressure urgency language to induce rushed user action without verification.",
                severity="high",
                confidence=0.88,
                risk_contribution=25
            ))
            evidence_items.append({"type": "URGENCY", "fact": "Urgency and account termination threats detected in body"})

        # 6. Credential Harvesting Lures
        cred_patterns = ["click here to verify", "reset your password", "confirm your identity", "update your credentials", "sign in to view", "login to re-activate"]
        if any(p in full_text for p in cred_patterns):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="credential_harvesting",
                title="Credential Verification Lure",
                description="Email instructs recipient to enter login credentials or click a verification link.",
                severity="high",
                confidence=0.90,
                risk_contribution=35
            ))
            evidence_items.append({"type": "CREDENTIAL_LURE", "fact": "Credential harvesting lure found in email body"})

        # 7. Financial & Invoice Fraud
        fin_patterns = ["invoice attached", "wire transfer", "payment overdue", "crypto refund", "payroll update", "remittance advice", "gift card"]
        if any(p in full_text for p in fin_patterns):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="financial_fraud",
                title="Financial Transaction Lure",
                description="The email references unauthorized billing, invoice payments, or money transfers.",
                severity="high",
                confidence=0.85,
                risk_contribution=30
            ))
            evidence_items.append({"type": "FINANCIAL_LURE", "fact": "Financial fraud indicators detected"})

        # Persist findings & evidence to database
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
                "sender": sender,
                "subject": subject,
                "reply_to": reply_to,
                "extracted_urls_count": len(extracted_urls),
                "extracted_urls": extracted_urls
            }
        )
