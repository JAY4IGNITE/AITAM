import asyncio
import logging
import json
import base64
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import httpx

try:
    import redis.asyncio as aioredis
except ImportError:
    import redis as aioredis

from ..schemas.threat_intel import ThreatIntelResult, Verdict, ThreatIntelProviderHealth
from ..models.threat_intel import ThreatIndicator
from ..database.connection import AsyncSessionLocal
from sqlalchemy.future import select

logger = logging.getLogger("threat_intel")
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "module": "threat_intel", "message": %(message)s}')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class ThreatIntelProvider:
    provider_name: str = "BaseProvider"
    provider_version: str = "1.0"
    supported_indicators: List[str] = []

    def __init__(self):
        self.enabled = True
        self.latency_ms = 0.0
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None
        
    async def lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        raise NotImplementedError
        
    async def health_check(self) -> bool:
        return True

class URLhausProvider(ThreatIntelProvider):
    """
    Real URLhaus Threat Intelligence Provider from abuse.ch.
    Queries URLhaus API for malicious URLs, payloads, and host reputations.
    Uses URLHAUS_AUTH_KEY from environment without exposing it to clients.
    """
    provider_name = "URLhaus"
    provider_version = "2.0.0"
    supported_indicators = ["URL", "DOMAIN", "IP", "HASH"]

    def __init__(self):
        super().__init__()
        self.auth_key = os.getenv("URLHAUS_AUTH_KEY") or os.getenv("URLHAUS_API_KEY", "")
        self.base_url = "https://urlhaus-api.abuse.ch/v1"

    async def lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        start_time = asyncio.get_event_loop().time()
        headers = {
            "User-Agent": "ThreatLens-SOC-Engine/2.0"
        }
        if self.auth_key:
            headers["Auth-Key"] = self.auth_key

        endpoint = f"{self.base_url}/url/"
        data: Dict[str, Any] = {}

        if indicator_type == "URL":
            endpoint = f"{self.base_url}/url/"
            data = {"url": indicator}
        elif indicator_type in ["DOMAIN", "IP"]:
            endpoint = f"{self.base_url}/host/"
            data = {"host": indicator}
        elif indicator_type == "HASH":
            endpoint = f"{self.base_url}/payload/"
            if len(indicator) == 64:
                data = {"sha256_hash": indicator}
            else:
                data = {"md5_hash": indicator}
        else:
            return self._unknown_result(indicator, indicator_type, "Unsupported indicator type for URLhaus")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(endpoint, data=data, headers=headers)
                
            end_time = asyncio.get_event_loop().time()
            self.latency_ms = (end_time - start_time) * 1000

            if resp.status_code != 200:
                self.last_error = f"HTTP {resp.status_code}"
                return self._unknown_result(indicator, indicator_type, f"URLhaus API returned HTTP {resp.status_code}")

            json_resp = resp.json()
            query_status = json_resp.get("query_status", "unknown")

            self.last_success = datetime.now(timezone.utc)
            self.last_error = None

            if query_status == "ok":
                # Found malicious record
                threat = json_resp.get("threat") or json_resp.get("url_status") or "malware"
                tags = json_resp.get("tags") or []
                url_status = json_resp.get("url_status", "unknown")
                reporter = json_resp.get("reporter", "URLhaus Community")
                
                evidence = [
                    f"Identified as active threat on URLhaus: {threat}",
                    f"Reported by {reporter} (status: {url_status})"
                ]
                if tags:
                    evidence.append(f"Associated malware tags: {', '.join(tags)}")

                return ThreatIntelResult(
                    provider=self.provider_name,
                    indicator_type=indicator_type,
                    indicator=indicator,
                    verdict=Verdict.MALICIOUS,
                    confidence=0.98,
                    reputation_score=10,
                    categories=["malware", "phishing"] + tags,
                    evidence=evidence,
                    first_seen=datetime.now(timezone.utc),
                    last_seen=datetime.now(timezone.utc),
                    lookup_timestamp=datetime.now(timezone.utc),
                    provider_metadata={
                        "threat": threat,
                        "url_status": url_status,
                        "tags": tags,
                        "urlhaus_reference": json_resp.get("urlhaus_reference")
                    }
                )
            elif query_status == "no_results":
                return ThreatIntelResult(
                    provider=self.provider_name,
                    indicator_type=indicator_type,
                    indicator=indicator,
                    verdict=Verdict.CLEAN,
                    confidence=0.70,
                    reputation_score=85,
                    categories=[],
                    evidence=["Not listed in URLhaus malicious dataset."],
                    lookup_timestamp=datetime.now(timezone.utc),
                    provider_metadata={"query_status": "no_results"}
                )
            else:
                return self._unknown_result(indicator, indicator_type, f"URLhaus query status: {query_status}")

        except httpx.TimeoutException:
            self.last_error = "Timeout"
            return self._unknown_result(indicator, indicator_type, "URLhaus request timed out")
        except Exception as e:
            self.last_error = str(e)
            return self._unknown_result(indicator, indicator_type, f"URLhaus error: {str(e)}")

    def _unknown_result(self, indicator: str, indicator_type: str, reason: str) -> ThreatIntelResult:
        return ThreatIntelResult(
            provider=self.provider_name,
            indicator_type=indicator_type,
            indicator=indicator,
            verdict=Verdict.UNKNOWN,
            confidence=0.0,
            reputation_score=50,
            categories=[],
            evidence=[reason],
            lookup_timestamp=datetime.now(timezone.utc),
            provider_metadata={"error": reason}
        )

class VirusTotalProvider(ThreatIntelProvider):
    """
    VirusTotal v3 Intelligence Provider.
    Queries VirusTotal for URLs, Domains, IPs, and Hashes.
    """
    provider_name = "VirusTotal"
    provider_version = "3.0.0"
    supported_indicators = ["URL", "DOMAIN", "IP", "HASH"]

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("VIRUSTOTAL_API_KEY", "")
        self.enabled = bool(self.api_key)

    async def lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        if not self.api_key:
            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                evidence=["VirusTotal API key not configured."],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata={"status": "not_configured"}
            )

        start_time = asyncio.get_event_loop().time()
        headers = {"x-apikey": self.api_key}

        url = ""
        if indicator_type == "URL":
            url_id = base64.urlsafe_b64encode(indicator.encode()).decode().strip("=")
            url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        elif indicator_type == "DOMAIN":
            url = f"https://www.virustotal.com/api/v3/domains/{indicator}"
        elif indicator_type == "IP":
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{indicator}"
        elif indicator_type == "HASH":
            url = f"https://www.virustotal.com/api/v3/files/{indicator}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, headers=headers)

            end_time = asyncio.get_event_loop().time()
            self.latency_ms = (end_time - start_time) * 1000

            if resp.status_code == 404:
                return ThreatIntelResult(
                    provider=self.provider_name,
                    indicator_type=indicator_type,
                    indicator=indicator,
                    verdict=Verdict.UNKNOWN,
                    confidence=0.5,
                    evidence=["Indicator not observed in VirusTotal dataset."],
                    lookup_timestamp=datetime.now(timezone.utc),
                    provider_metadata={"status": "not_found"}
                )
            elif resp.status_code != 200:
                self.last_error = f"HTTP {resp.status_code}"
                return ThreatIntelResult(
                    provider=self.provider_name,
                    indicator_type=indicator_type,
                    indicator=indicator,
                    verdict=Verdict.UNKNOWN,
                    confidence=0.0,
                    evidence=[f"VirusTotal API HTTP {resp.status_code}"],
                    lookup_timestamp=datetime.now(timezone.utc),
                    provider_metadata={"error": f"HTTP {resp.status_code}"}
                )

            data = resp.json().get("data", {}).get("attributes", {})
            stats = data.get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            harmless = stats.get("harmless", 0)

            self.last_success = datetime.now(timezone.utc)
            self.last_error = None

            evidence = [f"VirusTotal detection stats: {malicious} malicious, {suspicious} suspicious, {harmless} clean."]

            if malicious >= 3:
                verdict = Verdict.MALICIOUS
                confidence = min(0.99, 0.70 + (malicious * 0.03))
                reputation = max(5, 100 - (malicious * 10))
            elif malicious >= 1 or suspicious >= 2:
                verdict = Verdict.SUSPICIOUS
                confidence = 0.75
                reputation = 40
            elif harmless > 0:
                verdict = Verdict.CLEAN
                confidence = 0.85
                reputation = 90
            else:
                verdict = Verdict.UNKNOWN
                confidence = 0.5
                reputation = 50

            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=verdict,
                confidence=round(confidence, 2),
                reputation_score=reputation,
                categories=["security_vendors_flagged"] if malicious > 0 else [],
                evidence=evidence,
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata=stats
            )

        except Exception as e:
            self.last_error = str(e)
            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                evidence=[f"VirusTotal query failed: {str(e)}"],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata={"error": str(e)}
            )

class GoogleSafeBrowsingProvider(ThreatIntelProvider):
    """
    Google Safe Browsing API v4 Provider.
    Delegates to dedicated SafeBrowsingService.
    """
    provider_name = "GoogleSafeBrowsing"
    provider_version = "4.0.0"
    supported_indicators = ["URL"]

    def __init__(self):
        super().__init__()
        self.enabled = bool(os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", ""))

    async def lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        if indicator_type != "URL":
            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                evidence=["Google Safe Browsing only evaluates URL indicators."],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata={"status": "skipped"}
            )

        from ..services.safe_browsing import safe_browsing_service
        res = await safe_browsing_service.check_url(indicator)
        self.latency_ms = res.latency_ms
        self.last_error = res.error

        if res.threat_detected:
            self.last_success = datetime.now(timezone.utc)
            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.MALICIOUS,
                confidence=0.96,
                reputation_score=15,
                categories=res.threat_types,
                evidence=[f"Google Safe Browsing match: {', '.join(res.threat_types)} (Platform: {', '.join(res.platform_types) or 'ANY'})"],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata=res.model_dump(mode='json')
            )
        elif res.checked and res.safe:
            self.last_success = datetime.now(timezone.utc)
            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.CLEAN,
                confidence=0.75,
                reputation_score=90,
                categories=[],
                evidence=["No known Safe Browsing threat detected. (Note: does not guarantee URL is legitimate)"],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata=res.model_dump(mode='json')
            )
        else:
            err_desc = f"Google Safe Browsing unavailable ({res.error})" if res.error else "Safe Browsing check failed"
            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                reputation_score=50,
                categories=[],
                evidence=[err_desc],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata=res.model_dump(mode='json')
            )

class DatabaseThreatIntelProvider(ThreatIntelProvider):
    """
    Local PostgreSQL Threat Indicators Database Provider.
    Checks ingested URLhaus feeds and confirmed threat reports.
    """
    provider_name = "ThreatLens-LocalDB"
    provider_version = "2.0.0"
    supported_indicators = ["URL", "DOMAIN", "IP", "HASH", "EMAIL"]

    async def lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        start_time = asyncio.get_event_loop().time()
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ThreatIndicator).where(
                        ThreatIndicator.indicator == indicator,
                        ThreatIndicator.status == "ACTIVE"
                    ).limit(1)
                )
                match = result.scalar_one_or_none()

            end_time = asyncio.get_event_loop().time()
            self.latency_ms = (end_time - start_time) * 1000
            self.last_success = datetime.now(timezone.utc)
            self.last_error = None

            if match:
                verdict_map = {
                    "MALICIOUS": Verdict.MALICIOUS,
                    "SUSPICIOUS": Verdict.SUSPICIOUS,
                    "CLEAN": Verdict.CLEAN
                }
                verdict = verdict_map.get(match.classification.upper(), Verdict.UNKNOWN)
                return ThreatIntelResult(
                    provider=self.provider_name,
                    indicator_type=indicator_type,
                    indicator=indicator,
                    verdict=verdict,
                    confidence=match.confidence or 0.95,
                    reputation_score=10 if verdict == Verdict.MALICIOUS else 80,
                    categories=match.tags or [],
                    evidence=[f"Known indicator in ThreatLens database (source: {match.source}, tags: {', '.join(match.tags or [])})"],
                    first_seen=match.first_seen,
                    last_seen=match.last_seen,
                    lookup_timestamp=datetime.now(timezone.utc),
                    provider_metadata={"source": match.source, "tags": match.tags}
                )
            else:
                return ThreatIntelResult(
                    provider=self.provider_name,
                    indicator_type=indicator_type,
                    indicator=indicator,
                    verdict=Verdict.UNKNOWN,
                    confidence=0.5,
                    evidence=["Not found in local threat indicators repository."],
                    lookup_timestamp=datetime.now(timezone.utc),
                    provider_metadata={"found": False}
                )

        except Exception as e:
            self.last_error = str(e)
            return ThreatIntelResult(
                provider=self.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                evidence=[f"Database threat lookup error: {str(e)}"],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata={"error": str(e)}
            )

class ThreatIntelProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, ThreatIntelProvider] = {}
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis = aioredis.from_url(redis_url, decode_responses=True)
        except Exception:
            self.redis = None
        
    def register(self, provider: ThreatIntelProvider):
        self.providers[provider.provider_name] = provider
        logger.info(f'{{"event": "provider_registered", "provider": "{provider.provider_name}"}}')
        
    async def get_health(self) -> List[ThreatIntelProviderHealth]:
        health_list = []
        for name, p in self.providers.items():
            health_list.append(ThreatIntelProviderHealth(
                provider_name=name,
                enabled=p.enabled,
                status="Healthy" if p.last_error is None else f"Degraded ({p.last_error})",
                latency_ms=p.latency_ms,
                last_success=p.last_success,
                last_error=p.last_error
            ))
        return health_list

    async def lookup(self, indicator: str, indicator_type: str) -> List[ThreatIntelResult]:
        indicator_norm = indicator.strip()
        cache_key = f"threatintel:{indicator_type.upper()}:{indicator_norm}"
        
        # 1. Check Redis Cache
        if self.redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    logger.info(f'{{"event": "cache_hit", "indicator": "{indicator_norm}"}}')
                    cached_json = json.loads(cached_data)
                    return [ThreatIntelResult(**res) for res in cached_json]
            except Exception as e:
                logger.warning(f'{{"event": "cache_error", "error": "{str(e)}"}}')
            
        # 2. Gather Enabled Providers
        tasks = []
        for p in self.providers.values():
            if p.enabled and indicator_type.upper() in p.supported_indicators:
                tasks.append(self._safe_lookup(p, indicator_norm, indicator_type.upper()))
                
        # 3. Execute concurrently with timeout
        results: List[ThreatIntelResult] = []
        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for res in completed:
                if isinstance(res, ThreatIntelResult):
                    results.append(res)
                
        # 4. Save to Redis Cache if we got valid results
        if results and self.redis:
            try:
                await self.redis.setex(
                    cache_key, 
                    3600,  # 1 hour TTL
                    json.dumps([r.model_dump(mode='json') for r in results])
                )
            except Exception as e:
                logger.warning(f'{{"event": "cache_write_error", "error": "{str(e)}"}}')
                
        return results

    async def _safe_lookup(self, provider: ThreatIntelProvider, indicator: str, indicator_type: str) -> Optional[ThreatIntelResult]:
        try:
            return await asyncio.wait_for(provider.lookup(indicator, indicator_type), timeout=6.0)
        except asyncio.TimeoutError:
            provider.last_error = "Timeout"
            logger.error(f'{{"event": "provider_timeout", "provider": "{provider.provider_name}"}}')
            return ThreatIntelResult(
                provider=provider.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                evidence=[f"Provider {provider.provider_name} timed out after 6 seconds."],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata={"error": "timeout"}
            )
        except Exception as e:
            provider.last_error = str(e)
            logger.error(f'{{"event": "provider_error", "provider": "{provider.provider_name}", "error": "{str(e)}"}}')
            return ThreatIntelResult(
                provider=provider.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.UNKNOWN,
                confidence=0.0,
                evidence=[f"Provider {provider.provider_name} error: {str(e)}"],
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata={"error": str(e)}
            )

# Global Registry Instance with Real Providers
registry = ThreatIntelProviderRegistry()
registry.register(DatabaseThreatIntelProvider())
registry.register(URLhausProvider())
registry.register(VirusTotalProvider())
registry.register(GoogleSafeBrowsingProvider())
