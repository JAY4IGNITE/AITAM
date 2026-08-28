import asyncio
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..models.iocs import IOC
from ..schemas.agent_io import AgentResult
from ..engine.input_processor import UniversalInputProcessor
from ..engine.threat_intel_provider import registry
from ..engine.threat_intel_correlation import ThreatIntelCorrelationService
from ..schemas.threat_intel import Verdict

class ThreatIntelligenceAgent(BaseAgent):
    agent_name = "threat_intelligence"
    agent_version = "2.0.0"
    capabilities = ["domain_reputation", "ip_reputation", "url_reputation", "correlation"]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")
            
        content = inv.normalized_input or inv.target
        threat_obj = UniversalInputProcessor.process_input(inv.input_type, content)
        
        all_results = []
        
        # Parallel lookups for all extracted indicators
        lookup_tasks = []
        for ind in threat_obj.extracted_indicators:
            lookup_tasks.append(registry.lookup(ind.value, ind.type))
            
        if lookup_tasks:
            completed = await asyncio.gather(*lookup_tasks, return_exceptions=True)
            for res_list in completed:
                if isinstance(res_list, list):
                    all_results.extend(res_list)
                    
        # Group results by indicator for correlation
        results_by_indicator: Dict[str, list] = {}
        for r in all_results:
            if r.indicator not in results_by_indicator:
                results_by_indicator[r.indicator] = []
            results_by_indicator[r.indicator].append(r)
            
        findings = []
        evidence_list = []
        iocs_to_save = []
        
        for indicator, res_list in results_by_indicator.items():
            final_verdict, conf, correlation_evidence = ThreatIntelCorrelationService.correlate(res_list)
            
            if final_verdict in [Verdict.MALICIOUS, Verdict.SUSPICIOUS]:
                severity = "critical" if final_verdict == Verdict.MALICIOUS else "high"
                contribution = 60 if final_verdict == Verdict.MALICIOUS else 30
                
                title = f"{final_verdict.value.title()} indicator detected: {indicator}"
                desc = " | ".join(correlation_evidence)
                
                f = Finding(
                    investigation_id=investigation_id, 
                    agent=cls.agent_name, 
                    category="threat_intel",
                    title=title, 
                    description=desc,
                    severity=severity, 
                    confidence=conf, 
                    risk_contribution=contribution
                )
                findings.append(f)
                
                for ev in correlation_evidence:
                    evidence_list.append({"indicator": indicator, "fact": ev})
                    
                # Save IOC
                iocs_to_save.append(IOC(
                    investigation_id=investigation_id,
                    ioc_type=res_list[0].indicator_type,
                    value=indicator,
                    source_agent=cls.agent_name,
                    confidence=conf,
                    first_seen=datetime.utcnow().isoformat(),
                    last_seen=datetime.utcnow().isoformat()
                ))
                
                session.add(f)
                
        if findings:
            session.add_all(iocs_to_save)
            for ev_dict in evidence_list:
                session.add(Evidence(
                    investigation_id=investigation_id, 
                    agent_name=cls.agent_name,
                    evidence_type="THREAT_INTEL", 
                    severity="high", 
                    observed_fact=ev_dict["fact"], 
                    confidence=1.0
                ))
                
        return AgentResult(
            agent_name=cls.agent_name, 
            agent_version=cls.agent_version, 
            status="COMPLETED", 
            execution_time=0.0,
            findings=[{"title": f.title, "severity": f.severity, "category": f.category} for f in findings],
            evidence=evidence_list, 
            confidence=0.9
        )
