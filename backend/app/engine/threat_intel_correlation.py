from typing import List, Dict, Any, Tuple
from ..schemas.threat_intel import ThreatIntelResult, Verdict
from datetime import datetime, timezone

class ThreatIntelCorrelationService:
    @staticmethod
    def correlate(results: List[ThreatIntelResult]) -> Tuple[Verdict, float, List[str]]:
        if not results:
            return Verdict.UNKNOWN, 0.0, ["No threat intelligence results available."]
            
        valid_results = [r for r in results if r.verdict != Verdict.ERROR]
        if not valid_results:
            return Verdict.UNKNOWN, 0.0, ["All providers returned errors or timeouts."]
            
        malicious_count = sum(1 for r in valid_results if r.verdict == Verdict.MALICIOUS)
        suspicious_count = sum(1 for r in valid_results if r.verdict == Verdict.SUSPICIOUS)
        clean_count = sum(1 for r in valid_results if r.verdict == Verdict.CLEAN)
        
        total_valid = len(valid_results)
        evidence = []
        
        # Freshness Check (assuming anything older than 7 days is STALE)
        stale_count = 0
        now = datetime.now(timezone.utc)
        for r in valid_results:
            if r.lookup_timestamp:
                delta = now - r.lookup_timestamp
                if delta.days > 7:
                    stale_count += 1
                    evidence.append(f"{r.provider} intelligence is STALE (>7 days old).")
        
        # Calculate base confidence
        agreement_ratio = 0.0
        final_verdict = Verdict.UNKNOWN
        
        # Disagreement Handling
        if malicious_count > 0 and clean_count > 0:
            evidence.append(f"Threat intelligence sources disagree: {malicious_count} MALICIOUS, {clean_count} CLEAN.")
            # If providers disagree strongly, we downgrade to SUSPICIOUS / NEEDS REVIEW
            final_verdict = Verdict.SUSPICIOUS
            agreement_ratio = max(malicious_count, clean_count) / total_valid
            # Reduce confidence due to conflict
            base_confidence = agreement_ratio * 0.7 
        elif malicious_count > 0:
            final_verdict = Verdict.MALICIOUS
            agreement_ratio = malicious_count / total_valid
            base_confidence = 0.6 + (0.4 * agreement_ratio)
            evidence.append(f"{malicious_count}/{total_valid} independent providers flagged this indicator as MALICIOUS.")
        elif suspicious_count > 0:
            final_verdict = Verdict.SUSPICIOUS
            agreement_ratio = suspicious_count / total_valid
            base_confidence = 0.5 + (0.3 * agreement_ratio)
            evidence.append(f"{suspicious_count}/{total_valid} independent providers flagged this indicator as SUSPICIOUS.")
        elif clean_count == total_valid:
            final_verdict = Verdict.CLEAN
            agreement_ratio = 1.0
            base_confidence = 0.85
            evidence.append("All providers reported this indicator as CLEAN.")
        else:
            final_verdict = Verdict.UNKNOWN
            base_confidence = 0.0
            
        # Freshness Penalty
        if stale_count > 0:
            penalty = (stale_count / total_valid) * 0.2
            base_confidence = max(0.1, base_confidence - penalty)
            
        return final_verdict, round(base_confidence, 2), evidence
