import os
import re
import json
import hashlib
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse
import httpx
from pydantic import BaseModel, Field
from redis import Redis

logger = logging.getLogger("safe_browsing")
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "service": "safe_browsing", "message": "%(message)s"}')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class SafeBrowsingResult(BaseModel):
    """
    Normalized internal Google Safe Browsing assessment model.
    Never exposes raw provider responses or sensitive API keys.
    """
    url: str
    normalized_url: str
    checked: bool
    safe: Optional[bool] = None
    threat_detected: Optional[bool] = None
    threat_types: List[str] = Field(default_factory=list)
    platform_types: List[str] = Field(default_factory=list)
    cache_duration: Optional[str] = None
    source: str = "google_safe_browsing"
    error: Optional[str] = None
    latency_ms: Optional[float] = None
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SafeBrowsingService:
    """
    Dedicated Google Safe Browsing Service.
    Supports asynchronous URL verification, multi-URL batching, normalization,
    Redis caching, and graceful failure handling.
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", "")
        self.endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        self.client_id = "threatlens-soc"
        self.client_version = "2.0.0"
        self.timeout = 6.0
        self.last_error: Optional[str] = None
        self.latency_ms: Optional[float] = None
        
        # Redis cache connection
        self.redis_client = None
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = Redis.from_url(redis_url, decode_responses=True, socket_timeout=1.5)
        except Exception:
            self.redis_client = None

    def _get_api_key(self) -> str:
        """Dynamically retrieves API key from environment."""
        return os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", self.api_key or "")

    def normalize_url(self, raw_url: str) -> str:
        """
        Normalizes a URL before inspection:
        - Trims whitespace
        - Adds default http:// if protocol is missing
        - Safely lowercases hostname while preserving path and query arguments
        - Strips embedded basic-auth user:pass credentials for privacy
        """
        if not raw_url:
            return ""
        clean = raw_url.strip()
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+-.]*://', clean):
            clean = "http://" + clean
            
        try:
            parsed = urlparse(clean)
            # Remove basic auth userinfo
            netloc = parsed.netloc
            if "@" in netloc:
                netloc = netloc.split("@")[-1]
            netloc = netloc.lower()
            
            normalized = urlunparse((
                parsed.scheme.lower(),
                netloc,
                parsed.path or "/",
                parsed.params,
                parsed.query,
                ""  # Strip fragment
            ))
            return normalized
        except Exception:
            return clean

    def _get_cached_result(self, normalized_url: str) -> Optional[SafeBrowsingResult]:
        """Reads result from Redis cache if available."""
        if not self.redis_client:
            return None
        try:
            url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
            cached_json = self.redis_client.get(f"gsb_cache:{url_hash}")
            if cached_json:
                data = json.loads(cached_json)
                return SafeBrowsingResult(**data)
        except Exception:
            pass
        return None

    def _set_cached_result(self, result: SafeBrowsingResult, ttl_seconds: int = 3600):
        """Stores result in Redis cache with TTL."""
        if not self.redis_client or not result.checked:
            return
        try:
            url_hash = hashlib.sha256(result.normalized_url.encode()).hexdigest()
            self.redis_client.set(f"gsb_cache:{url_hash}", result.model_dump_json(), ex=ttl_seconds)
        except Exception:
            pass

    async def check_url(self, raw_url: str) -> SafeBrowsingResult:
        """
        Checks a single URL against Google Safe Browsing.
        Returns a normalized SafeBrowsingResult without throwing exceptions.
        """
        normalized = self.normalize_url(raw_url)
        if not normalized:
            return SafeBrowsingResult(
                url=raw_url,
                normalized_url="",
                checked=False,
                error="invalid_url"
            )

        # 1. Check cache first
        cached = self._get_cached_result(normalized)
        if cached:
            return cached

        api_key = self._get_api_key()
        if not api_key:
            logger.info("Safe Browsing check skipped: GOOGLE_SAFE_BROWSING_API_KEY not configured")
            return SafeBrowsingResult(
                url=raw_url,
                normalized_url=normalized,
                checked=False,
                error="not_configured"
            )

        payload = {
            "client": {
                "clientId": self.client_id,
                "clientVersion": self.client_version
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": normalized}]
            }
        }

        url_endpoint = f"{self.endpoint}?key={api_key}"
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info("Safe Browsing check started")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url_endpoint, json=payload)
                
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            self.latency_ms = latency

            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("matches", [])
                
                if matches:
                    threat_types = list({m.get("threatType") for m in matches if m.get("threatType")})
                    platform_types = list({m.get("platformType") for m in matches if m.get("platformType")})
                    cache_duration = matches[0].get("cacheDuration") if matches else None
                    
                    logger.warning(f"Safe Browsing threat detected: {', '.join(threat_types)}")
                    result = SafeBrowsingResult(
                        url=raw_url,
                        normalized_url=normalized,
                        checked=True,
                        safe=False,
                        threat_detected=True,
                        threat_types=threat_types,
                        platform_types=platform_types,
                        cache_duration=cache_duration,
                        latency_ms=latency,
                        error=None
                    )
                else:
                    logger.info("Safe Browsing no known threat detected")
                    result = SafeBrowsingResult(
                        url=raw_url,
                        normalized_url=normalized,
                        checked=True,
                        safe=True,
                        threat_detected=False,
                        threat_types=[],
                        platform_types=[],
                        latency_ms=latency,
                        error=None
                    )
                
                self._set_cached_result(result)
                self.last_error = None
                return result

            elif resp.status_code in [400, 403]:
                error_msg = "api_key_service_blocked" if "blocked" in resp.text.lower() else "invalid_api_key"
                self.last_error = f"HTTP {resp.status_code} ({error_msg})"
                logger.warning(f"Safe Browsing authorization notice: HTTP {resp.status_code}")
                return SafeBrowsingResult(
                    url=raw_url,
                    normalized_url=normalized,
                    checked=False,
                    error=error_msg,
                    latency_ms=latency
                )
            elif resp.status_code == 429:
                self.last_error = "rate_limited"
                logger.warning("Safe Browsing rate limit exceeded (HTTP 429)")
                return SafeBrowsingResult(
                    url=raw_url,
                    normalized_url=normalized,
                    checked=False,
                    error="rate_limited",
                    latency_ms=latency
                )
            else:
                self.last_error = f"HTTP {resp.status_code}"
                return SafeBrowsingResult(
                    url=raw_url,
                    normalized_url=normalized,
                    checked=False,
                    error="service_unavailable",
                    latency_ms=latency
                )

        except httpx.TimeoutException:
            self.last_error = "timeout"
            logger.warning("Safe Browsing request timed out")
            return SafeBrowsingResult(
                url=raw_url,
                normalized_url=normalized,
                checked=False,
                error="timeout"
            )
        except Exception as e:
            self.last_error = "request_failed"
            logger.warning(f"Safe Browsing request failed: {type(e).__name__}")
            return SafeBrowsingResult(
                url=raw_url,
                normalized_url=normalized,
                checked=False,
                error="request_failed"
            )

    async def check_urls(self, raw_urls: List[str]) -> List[SafeBrowsingResult]:
        """
        Evaluates multiple URLs concurrently and deduplicates repeated instances.
        """
        if not raw_urls:
            return []

        # Deduplicate by normalized URL
        seen = set()
        unique_urls = []
        for u in raw_urls:
            norm = self.normalize_url(u)
            if norm and norm not in seen:
                seen.add(norm)
                unique_urls.append(u)

        tasks = [self.check_url(u) for u in unique_urls]
        return await asyncio.gather(*tasks)

    async def health_check(self) -> Dict[str, Any]:
        """
        Returns live connectivity and operational health without leaking credentials.
        """
        api_key = self._get_api_key()
        configured = bool(api_key)
        
        if not configured:
            return {
                "provider": "GoogleSafeBrowsing",
                "configured": False,
                "status": "Not Configured",
                "latency_ms": None,
                "error": "GOOGLE_SAFE_BROWSING_API_KEY is not set in environment"
            }

        test_url = "http://testsafebrowsing.appspot.com/s/phishing.html"
        result = await self.check_url(test_url)
        
        status = "Healthy" if result.checked else f"Degraded ({result.error})"
        
        return {
            "provider": "GoogleSafeBrowsing",
            "configured": True,
            "status": status,
            "latency_ms": result.latency_ms or self.latency_ms,
            "error": result.error
        }

# Global singleton service instance
safe_browsing_service = SafeBrowsingService()
