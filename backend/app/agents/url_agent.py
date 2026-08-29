import re
import socket
import urllib.parse
from urllib.parse import urlparse, unquote
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentResult, Signal

# Curated lists of suspicious TLDs, URL shorteners, and brand keywords
SUSPICIOUS_TLDS = {
    "top", "xyz", "click", "buzz", "cfd", "rest", "gq", "tk", "ml", "ga", "cf",
    "icu", "cam", "loan", "men", "work", "fit", "surf", "cn", "ru", "su", "country",
    "stream", "download", "racing", "date", "faith", "party", "review", "trade", "accountant"
}

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd", "buff.ly", "ow.ly", "goo.gl",
    "cutt.ly", "rb.gy", "shorturl.at", "rebrand.ly", "bl.ink", "tiny.cc", "s.id"
}

HIGH_RISK_KEYWORDS = [
    "login", "signin", "sign-in", "log-in", "verify", "verification", "secure", "security",
    "account", "update", "banking", "auth", "authentication", "confirm", "confirmation",
    "password", "passwd", "credential", "wallet", "metamask", "coinbase", "binance",
    "suspended", "unlock", "recover", "recovery", "validation", "authenticate", "passcode",
    "billing", "invoice", "payment", "2fa", "mfa", "session", "support-desk"
]

class URLIntelligenceAgent(BaseAgent):
    agent_name = "url_intelligence"
    agent_version = "2.0.0"
    capabilities = [
        "url_decomposition", "punycode_detection", "ip_url_detection",
        "tld_reputation", "obfuscation_analysis", "brand_squatting", "shortener_detection"
    ]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")
            
        target = inv.normalized_input or inv.target
        if not target.startswith(("http://", "https://")):
            target = f"http://{target}"

        parsed = urlparse(target)
        scheme = parsed.scheme.lower()
        hostname = (parsed.hostname or "").lower()
        port = parsed.port
        path = parsed.path or ""
        query = parsed.query or ""
        fragment = parsed.fragment or ""

        # Normalize canonical target URL
        inv.normalized_input = target

        findings: list[Finding] = []
        evidence_items: list[dict] = []

        # 1. IP-based URL Detection
        is_ip = False
        try:
            socket.inet_aton(hostname)
            is_ip = True
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="evasion",
                title="Direct IP-based URL detected",
                description=f"Host '{hostname}' connects directly to an IP address rather than a domain name, bypassing DNS reputation filters.",
                severity="high",
                confidence=1.0,
                risk_contribution=35
            ))
            evidence_items.append({"type": "IP_HOST", "fact": f"Raw IPv4 host '{hostname}' used in target URL"})
        except (socket.error, OSError):
            pass

        # 2. Punycode / IDN Homograph Obfuscation Detection
        if hostname.startswith("xn--") or "xn--" in hostname:
            try:
                decoded_idn = hostname.encode('ascii').decode('idna')
                findings.append(Finding(
                    investigation_id=investigation_id,
                    agent=cls.agent_name,
                    category="evasion",
                    title="Punycode / IDN Homograph Domain Detected",
                    description=f"Domain '{hostname}' uses IDN Punycode to render international characters ('{decoded_idn}'), commonly used for lookalike brand spoofing.",
                    severity="critical",
                    confidence=0.98,
                    risk_contribution=45
                ))
                evidence_items.append({"type": "PUNYCODE", "fact": f"Punycode domain decoded to: '{decoded_idn}'"})
            except Exception:
                pass

        # 3. Suspicious TLD Detection
        if not is_ip and "." in hostname:
            tld = hostname.split(".")[-1]
            if tld in SUSPICIOUS_TLDS:
                findings.append(Finding(
                    investigation_id=investigation_id,
                    agent=cls.agent_name,
                    category="suspicious_infrastructure",
                    title=f"High-Risk TLD (.{tld}) Detected",
                    description=f"The top-level domain '.{tld}' exhibits disproportionately high rates of spam and phishing campaigns in global threat telemetry.",
                    severity="medium",
                    confidence=0.85,
                    risk_contribution=25
                ))
                evidence_items.append({"type": "SUSPICIOUS_TLD", "fact": f"High-risk top-level domain '.{tld}'"})

        # 4. Excessive Subdomain Nesting
        if not is_ip:
            subdomain_parts = hostname.split(".")
            if len(subdomain_parts) >= 5:
                findings.append(Finding(
                    investigation_id=investigation_id,
                    agent=cls.agent_name,
                    category="evasion",
                    title=f"Excessive Subdomain Depth ({len(subdomain_parts)} parts)",
                    description=f"Host '{hostname}' has {len(subdomain_parts)} subdomain components, typically used to disguise malicious destinations behind legitimate wildcard DNS.",
                    severity="medium",
                    confidence=0.90,
                    risk_contribution=20
                ))
                evidence_items.append({"type": "SUBDOMAINS", "fact": f"{len(subdomain_parts)} subdomain labels found in '{hostname}'"})

        # 5. Non-Standard Port
        if port and port not in [80, 443, 8080]:
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="suspicious_infrastructure",
                title=f"Non-Standard Port ({port}) Detected",
                description=f"URL targets non-standard HTTP port {port}, frequently used by rogue command-and-control or staging servers.",
                severity="medium",
                confidence=0.95,
                risk_contribution=20
            ))
            evidence_items.append({"type": "PORT", "fact": f"Non-standard HTTP port: {port}"})

        # 6. URL Shortener Detection
        if any(shortener in hostname for shortener in KNOWN_SHORTENERS):
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="evasion",
                title="URL Shortening Service Used",
                description=f"URL uses known shortening service '{hostname}', hiding the destination domain and redirect path.",
                severity="medium",
                confidence=1.0,
                risk_contribution=25
            ))
            evidence_items.append({"type": "SHORTENER", "fact": f"Known URL shortener: '{hostname}'"})

        # 7. URL Obfuscation & Suspicious Characters
        unquoted_target = unquote(target)
        if "%" in target and unquoted_target != target:
            # Check for double percent-encoding
            double_unquoted = unquote(unquoted_target)
            is_double = double_unquoted != unquoted_target
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="evasion",
                title="Double Percent-Encoding Obfuscation" if is_double else "Hex Encoded Obfuscation",
                description="The URL contains encoded character sequences designed to bypass signature and keyword filters.",
                severity="medium" if is_double else "low",
                confidence=0.90,
                risk_contribution=20 if is_double else 10
            ))
            evidence_items.append({"type": "ENCODING", "fact": f"Decoded URL: {unquoted_target}"})

        if "@" in target.split("?")[0]:
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="evasion",
                title="Userinfo '@' Symbol in URL Authority",
                description="URL contains '@' in the authority component, an old browser trick to misdirect users about the actual destination hostname.",
                severity="high",
                confidence=0.95,
                risk_contribution=35
            ))
            evidence_items.append({"type": "MISDIRECTION", "fact": "URL uses '@' authority separator"})

        # 8. High-Risk Phishing Keywords in Hostname/Path/Query
        full_url_lower = unquoted_target.lower()
        matched_keywords = []
        for kw in HIGH_RISK_KEYWORDS:
            # Check if keyword is present as a token or substring in host or path
            if kw in hostname or kw in path.lower() or kw in query.lower():
                matched_keywords.append(kw)

        if matched_keywords:
            unique_kw = list(dict.fromkeys(matched_keywords))[:5]
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="social_engineering",
                title=f"Credential Lure Keywords: {', '.join(unique_kw[:3])}",
                description=f"The URL path and domain contain credential harvesting lures: {', '.join(unique_kw)}.",
                severity="high",
                confidence=0.92,
                risk_contribution=min(40, len(unique_kw) * 15)
            ))
            evidence_items.append({"type": "KEYWORDS", "fact": f"Detected lure keywords: {', '.join(unique_kw)}"})

        # Save findings to DB
        if findings:
            session.add_all(findings)
            for ev in evidence_items:
                session.add(Evidence(
                    investigation_id=investigation_id,
                    agent_name=cls.agent_name,
                    evidence_type=ev["type"],
                    severity="high" if any(f.severity == "high" for f in findings) else "medium",
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
                "scheme": scheme,
                "hostname": hostname,
                "port": port,
                "path": path,
                "is_ip": is_ip,
                "subdomains_count": len(hostname.split(".")) if not is_ip else 0,
                "matched_keywords": matched_keywords
            }
        )
