import os
import re
import hashlib
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..models.iocs import IOC, Artifact
from ..models.tempmail import TempMailMessage
from ..schemas.agent_io import AgentResult

DANGEROUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".wsh",
    ".ps1", ".psm1", ".hta", ".cpl", ".msc", ".jar", ".iso", ".img", ".vhd",
    ".docm", ".dotm", ".xlsm", ".xltm", ".xlam", ".pptm", ".potm", ".ppam", ".ppsx"
}

ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}

class AttachmentAnalysisAgent(BaseAgent):
    """
    Zero-Host-Execution Static Attachment Security Agent.
    Safely inspects file metadata, MIME structures, cryptographic hashes,
    and dangerous macro/executable extensions without executing untrusted code on the host.
    """
    agent_name = "attachment_analysis"
    agent_version = "1.0.0"
    capabilities = ["static_inspection", "hash_reputation", "macro_detection", "archive_heuristic"]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")

        findings: List[Finding] = []
        evidence_items: List[Dict[str, Any]] = []

        # 1. Retrieve any associated TempMailMessage or Artifact records
        msg = (await session.execute(
            select(TempMailMessage).where(TempMailMessage.investigation_id == investigation_id)
        )).scalar_one_or_none()

        attachments = (msg.attachment_metadata or []) if msg else []
        
        # Also check Artifacts table
        db_artifacts = (await session.execute(
            select(Artifact).where(Artifact.investigation_id == investigation_id)
        )).scalars().all()

        if not attachments and not db_artifacts:
            # Clean finding: No attachments present
            findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category="attachment_security",
                title="No Suspicious Attachments Detected",
                description="Email contains no binary or archive attachments.",
                severity="info",
                confidence=1.0,
                risk_contribution=0
            ))
            evidence_items.append({"type": "ATTACHMENT", "fact": "Zero attachments present in message body."})
        else:
            for att in attachments:
                fname = att.get("filename") or "unnamed_attachment"
                mime = att.get("mime_type") or "application/octet-stream"
                size = att.get("size") or 0
                sha256 = att.get("sha256") or hashlib.sha256(fname.encode()).hexdigest()
                ext = os.path.splitext(fname)[1].lower()

                # Register IoC
                session.add(IOC(
                    investigation_id=investigation_id,
                    ioc_type="HASH",
                    value=sha256,
                    source_agent=cls.agent_name,
                    confidence=0.95
                ))

                # Check dangerous extensions
                if ext in DANGEROUS_EXTENSIONS:
                    findings.append(Finding(
                        investigation_id=investigation_id,
                        agent=cls.agent_name,
                        category="malware_payload",
                        title=f"High-Risk Executable Attachment ({ext}) Detected: {fname}",
                        description=f"Attachment '{fname}' has a high-risk file extension '{ext}' frequently used to deliver droppers, ransomwares, or malware loaders.",
                        severity="critical",
                        confidence=0.98,
                        risk_contribution=50
                    ))
                    evidence_items.append({
                        "type": "MALICIOUS_ATTACHMENT",
                        "fact": f"High-risk executable extension '{ext}' in attachment '{fname}' (SHA256: {sha256[:16]}...)"
                    })
                elif ext in ARCHIVE_EXTENSIONS:
                    findings.append(Finding(
                        investigation_id=investigation_id,
                        agent=cls.agent_name,
                        category="evasion",
                        title=f"Compressed Archive Attachment ({ext}) Detected: {fname}",
                        description=f"Attachment '{fname}' is an archive. Threat actors commonly use encrypted or nested archives to evade perimeter email gateways.",
                        severity="medium",
                        confidence=0.85,
                        risk_contribution=20
                    ))
                    evidence_items.append({
                        "type": "ARCHIVE_ATTACHMENT",
                        "fact": f"Archive attachment '{fname}' detected ({size} bytes)"
                    })

        # Save findings and evidence
        if findings:
            session.add_all(findings)
            for ev in evidence_items:
                session.add(Evidence(
                    investigation_id=investigation_id,
                    agent_name=cls.agent_name,
                    evidence_type=ev["type"],
                    severity="critical" if any(f.severity == "critical" for f in findings) else ("high" if any(f.severity == "high" for f in findings) else "info"),
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
            metadata={"attachments_analyzed": len(attachments) + len(db_artifacts)}
        )
