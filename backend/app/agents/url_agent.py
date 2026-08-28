import re
import socket
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse, unquote
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentOutput, Signal

class URLIntelligenceAgent(BaseAgent):
    agent_name = "url_intelligence"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        if inv.input_type.value not in ["URL", "WEBPAGE"]:
            run.outputs = {"message": "Input is not a URL"}
            run.confidence = 1.0
            return
            
        url = inv.target
        parsed = urlparse(url)
        
        # 1. Normalize URL
        hostname = parsed.hostname or ""
        path = parsed.path or ""
        port = parsed.port
        inv.normalized_input = f"{parsed.scheme}://{hostname}{path}"
        
        findings = []
        
        # 2. Detect IP-based URLs
        is_ip = False
        try:
            socket.inet_aton(hostname)
            is_ip = True
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="evasion",
                title="IP-based URL detected",
                description="The URL uses a raw IP address instead of a domain name, a common phishing tactic to evade domain reputation checks.",
                severity="high",
                confidence=1.0,
                risk_contribution=40
            ))
        except socket.error:
            pass

        # 3. Detect suspicious ports
        if port and port not in [80, 443]:
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="suspicious_infrastructure",
                title="Suspicious Port",
                description=f"The URL connects over a non-standard port ({port}) instead of HTTP/HTTPS.",
                severity="medium",
                confidence=1.0,
                risk_contribution=20
            ))
            
        # 4. Detect excessive subdomains
        subdomains = hostname.split('.')
        if not is_ip and len(subdomains) >= 5:
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="evasion",
                title="Excessive Subdomains",
                description=f"The hostname '{hostname}' contains {len(subdomains)} parts. Attackers use deep subdomains to hide malicious infrastructure.",
                severity="medium",
                confidence=0.9,
                risk_contribution=25
            ))
            
        # 5. Detect suspicious encoding
        if "%" in url:
            decoded = unquote(url)
            if decoded != url:
                findings.append(Finding(
                    investigation_id=investigation_id,
                    agent=cls.agent_name,
                    category="evasion",
                    title="URL Encoding Obfuscation",
                    description="The URL contains encoded characters, which can be used to bypass security filters.",
                    severity="low",
                    confidence=0.8,
                    risk_contribution=10
                ))
                
        # 6. Detect URL shorteners
        shorteners = ["bit.ly", "tinyurl.com", "t.co", "is.gd", "buff.ly", "ow.ly", "goo.gl"]
        if any(shortener in hostname.lower() for shortener in shorteners):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="evasion",
                title="URL Shortener Used",
                description="The URL points to a known link shortener, hiding the true destination.",
                severity="medium",
                confidence=1.0,
                risk_contribution=25
            ))
            
        # 7. Identify suspicious patterns (Typosquatting/keywords)
        suspicious_keywords = ["login", "verify", "secure", "account", "update", "banking", "auth", "confirm"]
        for kw in suspicious_keywords:
            if kw in hostname.lower() or kw in path.lower():
                findings.append(Finding(
                    investigation_id=investigation_id,
                    agent=cls.agent_name,
                    category="social_engineering",
                    title="Suspicious Keyword",
                    description=f"The URL contains the keyword '{kw}', frequently used in credential harvesting lures.",
                    severity="high",
                    confidence=0.95,
                    risk_contribution=35
                ))
        
        # Save findings to DB
        session.add_all(findings)
        
        # Calculate mock aggregate logic for backwards compatibility with RiskEngine
        total_risk = min(100, sum(f.risk_contribution for f in findings))
        signals = [Signal(type=f.category, severity=f.severity, evidence=f.title) for f in findings]
        
        output = AgentOutput(
            agent_name=cls.agent_name,
            risk_score=float(total_risk),
            confidence=0.95,
            signals=signals
        )
            
        run.outputs = output.dict()
        run.confidence = output.confidence
        
        # Save legacy evidence (for backwards compatibility)
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
