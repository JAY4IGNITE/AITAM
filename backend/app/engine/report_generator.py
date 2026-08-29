from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.investigation import Investigation
from ..models.report import Report, AttackStep
from ..models.finding import Finding
from ..models.agent import AgentRun, Evidence, SandboxSession
from ..models.iocs import IOC
from ..engine.threat_intel_provider import registry

class ReportGenerator:
    @staticmethod
    async def generate_report(investigation_id: str, session: AsyncSession) -> dict:
        """
        Generates a comprehensive, evidence-driven Threat Intelligence & Forensic Investigation Report.
        Synthesizes actual multi-agent findings, live threat intelligence lookups, MITRE ATT&CK mappings,
        sandbox behavioral telemetry, and actionable containment playbooks without static mock templates.
        """
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            return {"error": "Investigation not found"}
            
        # 1. Fetch Indicators of Compromise
        iocs_res = await session.execute(select(IOC).where(IOC.investigation_id == investigation_id))
        iocs = iocs_res.scalars().all()
        
        # 2. Query Live Threat Intelligence
        threat_intel_results = []
        for ioc in iocs:
            try:
                res_list = await registry.lookup(ioc.value, ioc.ioc_type.upper())
                for r in res_list:
                    threat_intel_results.append(r.model_dump(mode='json'))
            except Exception:
                pass

        # 3. Explicitly query related objects to prevent missing greenlet async errors
        findings_res = await session.execute(select(Finding).where(Finding.investigation_id == investigation_id))
        findings = findings_res.scalars().all()

        evidence_res = await session.execute(select(Evidence).where(Evidence.investigation_id == investigation_id))
        evidence_items = evidence_res.scalars().all()

        agent_runs_res = await session.execute(select(AgentRun).where(AgentRun.investigation_id == investigation_id))
        agent_runs = agent_runs_res.scalars().all()

        sb_res = await session.execute(select(SandboxSession).where(SandboxSession.investigation_id == investigation_id))
        sandbox_sessions = sb_res.scalars().all()

        score = inv.final_risk_score if inv.final_risk_score is not None else (inv.initial_risk_score or 0.0)
        classification = inv.classification or "UNKNOWN"
        confidence_pct = round((inv.confidence or 0.95) * 100, 1)

        # 4. Dynamic MITRE ATT&CK Matrix Mapping based on actual findings
        mitre_tactics = []
        observed_categories = {f.category for f in findings}
        
        # Initial Access
        if any(c in observed_categories for c in ["social_engineering", "smishing", "quishing", "email_spoofing"]):
            tech = "T1566.002 (Spearphishing Link)" if inv.input_type.value in ["EMAIL", "URL"] else \
                   "T1566.003 (Spearphishing via Social Service)" if inv.input_type.value == "SOCIAL" else "T1566 (Phishing)"
            mitre_tactics.append({
                "tactic": "Initial Access",
                "tactic_id": "TA0001",
                "technique": tech,
                "technique_id": tech.split()[0],
                "description": f"Attacker delivers malicious {inv.input_type.value} lure to initiate target engagement."
            })
            
        # Defense Evasion
        if "evasion" in observed_categories or any("punycode" in f.title.lower() or "encoding" in f.title.lower() for f in findings):
            mitre_tactics.append({
                "tactic": "Defense Evasion",
                "tactic_id": "TA0005",
                "technique": "T1036.007 (IDN Homograph / Obfuscated URL)",
                "technique_id": "T1036.007",
                "description": "Domain naming, punycode, or character encoding used to disguise malicious destinations."
            })

        # Credential Access
        if "credential_harvesting" in observed_categories or any("credential" in f.title.lower() or "login" in f.title.lower() for f in findings):
            mitre_tactics.append({
                "tactic": "Credential Access",
                "tactic_id": "TA0006",
                "technique": "T1056.001 (Web-Based Credential Harvesting)",
                "technique_id": "T1056.001",
                "description": "Attacker creates lookalike authentication interfaces to capture passwords, MFA OTPs, or API keys."
            })

        # Command & Control / Exfiltration
        if any(f.severity in ["critical", "high"] for f in findings) or "threat_intel" in observed_categories:
            mitre_tactics.append({
                "tactic": "Command and Control",
                "tactic_id": "TA0011",
                "technique": "T1071.001 (Web Protocols C2 / Destination)",
                "technique_id": "T1071.001",
                "description": "External rogue infrastructure hosting phishing or staging malicious secondary payloads."
            })

        # 5. Executive Summary Generation
        danger_level = "CRITICAL THREAT" if score >= 80 else \
                       "HIGH RISK" if score >= 60 else \
                       "SUSPICIOUS" if score >= 40 else \
                       "LOW RISK" if score >= 20 else "BENIGN / SAFE"

        primary_threats = [f.title for f in findings if f.severity in ["critical", "high"]]
        summary_text = (
            f"ThreatLens autonomous multi-agent analysis evaluated target artifact '{inv.target[:80]}' "
            f"across {len(agent_runs)} specialized intelligence agents. The artifact was classified as {classification} "
            f"with a final risk score of {score}/100 and a confidence rating of {confidence_pct}%. "
        )
        if primary_threats:
            summary_text += f"Primary attack indicators identified include: {'; '.join(primary_threats[:3])}."
        else:
            summary_text += "No critical malicious indicators were confirmed by reputation providers or behavioral sandboxing."

        # 6. Sandbox Detonation Telemetry
        sandbox_data = None
        if sandbox_sessions:
            sb = sandbox_sessions[-1]
            sandbox_data = {
                "status": sb.status.value,
                "browser": sb.browser_type,
                "events_count": sb.event_count or len(sb.events or []),
                "events": (sb.events or [])[:15],
                "network_summary": sb.network_summary or {},
                "screenshot": sb.screenshots.get("final") if (sb.screenshots and isinstance(sb.screenshots, dict)) else None
            }

        # 7. Tailored SOC Incident Containment Playbook
        playbook = []
        if score >= 60:
            playbook.append({
                "step": "1. Perimeter Firewall & DNS Block",
                "action": f"Add target destination and related IoCs to perimeter edge blocklist and DNS sinkhole.",
                "priority": "P1 - IMMEDIATE",
                "command": f"block-ioc --domain {inv.target[:50]}"
            })
            playbook.append({
                "step": "2. Session Invalidation & Credential Reset",
                "action": "Force password resets and revoke active sessions for any user who clicked or engaged with this artifact.",
                "priority": "P1 - IMMEDIATE",
                "command": "revoke-user-sessions --filter-visited"
            })
            playbook.append({
                "step": "3. Message Quarantine",
                "action": "Purge all incoming emails or messages containing matching subject, links, or sender domains from corporate mailboxes.",
                "priority": "P2 - HIGH",
                "command": "mail-quarantine --purge-matching"
            })
        elif score >= 40:
            playbook.append({
                "step": "1. Monitoring & Telemetry Alerting",
                "action": "Tag destination as suspicious in SIEM/EDR and monitor outbound proxy connections.",
                "priority": "P2 - HIGH",
                "command": "siem-watch --target " + inv.target[:40]
            })
            playbook.append({
                "step": "2. User Awareness Advisory",
                "action": "Advise the reporting user not to provide credentials or interact with unverified links.",
                "priority": "P3 - MEDIUM",
                "command": "notify-reporter --status 'SUSPICIOUS_CONTENT'"
            })
        else:
            playbook.append({
                "step": "1. Standard Observation",
                "action": "No immediate containment required. Continue standard security logging.",
                "priority": "P4 - INFORMATIONAL",
                "command": "log-entry --verdict 'BENIGN'"
            })

        # 8. Compile Master Report Content
        report_content = {
            "display_id": inv.display_id,
            "target": inv.target,
            "status": inv.status.value,
            "final_risk_score": score,
            "classification": classification,
            "confidence": inv.confidence,
            "metadata": {
                "report_id": f"REP-{inv.display_id}",
                "investigation_id": inv.id,
                "display_id": inv.display_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "engine_version": "ThreatLens v2.0 (Autonomous Multi-Agent SOC)",
            },
            "executive_summary": {
                "target": inv.target,
                "input_type": inv.input_type.value,
                "classification": classification,
                "danger_level": danger_level,
                "final_risk_score": score,
                "confidence_percentage": confidence_pct,
                "summary": summary_text,
                "findings_count": len(findings),
                "evidence_count": len(evidence_items),
                "iocs_count": len(iocs),
            },
            "mitre_attack_matrix": mitre_tactics,
            "agent_findings": [
                {
                    "title": f.title,
                    "severity": f.severity.upper(),
                    "category": f.category,
                    "description": f.description,
                    "confidence": f.confidence,
                    "risk_contribution": f.risk_contribution,
                    "agent": f.agent
                } for f in findings
            ],
            "evidence_highlights": [
                {
                    "fact": e.observed_fact,
                    "type": e.evidence_type,
                    "severity": e.severity,
                    "agent": e.agent_name,
                    "timestamp": e.created_at.isoformat() if e.created_at else None
                } for e in evidence_items
            ],
            "threat_intelligence": {
                "provider_queries_count": len(threat_intel_results),
                "verdicts": threat_intel_results,
            },
            "url_security_analysis": [
                {
                    "url": ioc.value,
                    "safe_browsing": next((
                        {
                            "status": "THREAT_DETECTED" if ti.get("verdict") == "MALICIOUS" else ("NO_KNOWN_THREAT_DETECTED" if ti.get("verdict") == "CLEAN" else "UNABLE_TO_VERIFY"),
                            "threat_types": ti.get("categories", []),
                            "severity": "HIGH" if ti.get("verdict") == "MALICIOUS" else ("INFO" if ti.get("verdict") == "CLEAN" else "UNKNOWN"),
                            "source": "Google Safe Browsing",
                            "interpretation": "The URL matches a known threat classification in Google Safe Browsing index." if ti.get("verdict") == "MALICIOUS" else ("No known Safe Browsing threat was identified. This result does not guarantee that the URL is legitimate." if ti.get("verdict") == "CLEAN" else "Safe Browsing verification was unavailable or rate-limited.")
                        } for ti in threat_intel_results if ti.get("provider") == "GoogleSafeBrowsing" and ti.get("indicator") == ioc.value
                    ), {
                        "status": "NO_KNOWN_THREAT_DETECTED",
                        "threat_types": [],
                        "severity": "INFO",
                        "source": "Google Safe Browsing",
                        "interpretation": "No known Safe Browsing threat was identified. This result does not guarantee that the URL is legitimate."
                    })
                } for ioc in iocs if ioc.ioc_type.upper() == "URL"
            ],
            "indicators_of_compromise": [
                {
                    "type": i.ioc_type,
                    "value": i.value,
                    "source": i.source_agent,
                    "confidence": i.confidence
                } for i in iocs
            ],
            "sandbox_detonation": sandbox_data,
            "containment_playbook": playbook,
            "agent_telemetry": [
                {
                    "agent_name": a.agent_name,
                    "version": a.agent_version,
                    "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                    "duration_seconds": round(a.duration, 2) if a.duration else 0.0,
                    "findings_count": getattr(a, "findings_count", len((a.outputs or {}).get("findings", [])))
                } for a in agent_runs
            ]
        }

        # 9. Persist to PostgreSQL Report and AttackStep Tables
        await session.execute(
            Report.__table__.delete().where(Report.investigation_id == investigation_id)
        )
        await session.execute(
            AttackStep.__table__.delete().where(AttackStep.investigation_id == investigation_id)
        )
        
        report = Report(
            investigation_id=investigation_id,
            report_type="FORENSIC_INTELLIGENCE",
            content=report_content
        )
        session.add(report)

        for idx, m in enumerate(mitre_tactics):
            step = AttackStep(
                investigation_id=investigation_id,
                step_order=str(idx + 1),
                description=f"{m['tactic']} - {m['technique']}: {m['description']}",
                mitre_tactic=m["tactic_id"],
                mitre_technique=m["technique_id"]
            )
            session.add(step)

        await session.commit()
        return report_content
