import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import os

try:
    import redis.asyncio as redis
except ImportError:
    import redis

from ..schemas.threat_intel import ThreatIntelResult, Verdict, ThreatIntelProviderHealth

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

class MockThreatIntelProvider(ThreatIntelProvider):
    provider_name = "MockThreatIntel"
    provider_version = "1.0"
    supported_indicators = ["URL", "DOMAIN", "IP", "HASH", "EMAIL"]

    async def lookup(self, indicator: str, indicator_type: str) -> ThreatIntelResult:
        start_time = asyncio.get_event_loop().time()
        
        # Simulate network delay
        await asyncio.sleep(0.05)
        
        indicator_lower = indicator.lower()
        verdict = Verdict.UNKNOWN
        conf = 0.5
        cats = []
        ev = []
        
        if "malicious" in indicator_lower or "123.45" in indicator_lower:
            verdict = Verdict.MALICIOUS
            conf = 0.99
            cats = ["malware", "phishing"]
            ev = ["Known malware distribution domain"]
        elif "suspicious" in indicator_lower or "scam" in indicator_lower:
            verdict = Verdict.SUSPICIOUS
            conf = 0.75
            cats = ["spam"]
            ev = ["Recently registered domain with low reputation"]
        elif "clean" in indicator_lower or "safe" in indicator_lower:
            verdict = Verdict.CLEAN
            conf = 0.95
            ev = ["No malicious activity observed"]
        elif "timeout" in indicator_lower:
            self.last_error = "Timeout"
            raise TimeoutError("Mock Provider Timeout")
            
        end_time = asyncio.get_event_loop().time()
        self.latency_ms = (end_time - start_time) * 1000
        self.last_success = datetime.now(timezone.utc)
        self.last_error = None
        
        return ThreatIntelResult(
            provider=self.provider_name,
            indicator_type=indicator_type,
            indicator=indicator,
            verdict=verdict,
            confidence=conf,
            reputation_score=10 if verdict == Verdict.MALICIOUS else (90 if verdict == Verdict.CLEAN else 50),
            categories=cats,
            evidence=ev,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            lookup_timestamp=datetime.now(timezone.utc),
            provider_metadata={"mock": True}
        )

class ThreatIntelProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, ThreatIntelProvider] = {}
        redis_host = os.environ.get("REDIS_HOST", "redis")
        self.redis = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
        
    def register(self, provider: ThreatIntelProvider):
        self.providers[provider.provider_name] = provider
        logger.info(f'{{"event": "provider_registered", "provider": "{provider.provider_name}"}}')
        
    async def get_health(self) -> List[ThreatIntelProviderHealth]:
        health_list = []
        for name, p in self.providers.items():
            health_list.append(ThreatIntelProviderHealth(
                provider_name=name,
                enabled=p.enabled,
                status="Healthy" if p.last_error is None else "Degraded",
                latency_ms=p.latency_ms,
                last_success=p.last_success,
                last_error=p.last_error
            ))
        return health_list

    async def lookup(self, indicator: str, indicator_type: str) -> List[ThreatIntelResult]:
        # 1. Check Cache
        cache_key = f"threatintel:{indicator_type}:{indicator}"
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                logger.info(f'{{"event": "cache_hit", "indicator": "{indicator}"}}')
                cached_json = json.loads(cached_data)
                return [ThreatIntelResult(**res) for res in cached_json]
        except Exception as e:
            logger.warning(f'{{"event": "cache_error", "error": "{str(e)}"}}')
            
        logger.info(f'{{"event": "cache_miss", "indicator": "{indicator}"}}')
            
        results = []
        tasks = []
        
        # 2. Gather Providers
        for p in self.providers.values():
            if p.enabled and indicator_type in p.supported_indicators:
                tasks.append(self._safe_lookup(p, indicator, indicator_type))
                
        # 3. Execute concurrently
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in completed:
            if isinstance(res, ThreatIntelResult):
                results.append(res)
                
        # 4. Save to Cache if we got results
        if results:
            try:
                # TTL 1 hour (3600 seconds)
                await self.redis.setex(
                    cache_key, 
                    3600, 
                    json.dumps([r.model_dump(mode='json') for r in results])
                )
            except Exception as e:
                logger.warning(f'{{"event": "cache_write_error", "error": "{str(e)}"}}')
                
        return results

    async def _safe_lookup(self, provider: ThreatIntelProvider, indicator: str, indicator_type: str) -> Optional[ThreatIntelResult]:
        try:
            # Enforce provider-level timeout
            return await asyncio.wait_for(provider.lookup(indicator, indicator_type), timeout=5.0)
        except asyncio.TimeoutError:
            provider.last_error = "Timeout"
            logger.error(f'{{"event": "provider_timeout", "provider": "{provider.provider_name}"}}')
            return ThreatIntelResult(
                provider=provider.provider_name,
                indicator_type=indicator_type,
                indicator=indicator,
                verdict=Verdict.ERROR,
                confidence=0.0,
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
                verdict=Verdict.ERROR,
                confidence=0.0,
                lookup_timestamp=datetime.now(timezone.utc),
                provider_metadata={"error": str(e)}
            )

# Global Registry Instance
registry = ThreatIntelProviderRegistry()
registry.register(MockThreatIntelProvider())
