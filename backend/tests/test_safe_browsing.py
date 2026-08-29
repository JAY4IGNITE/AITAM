import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.safe_browsing import SafeBrowsingService, SafeBrowsingResult
from app.engine.threat_intel_provider import GoogleSafeBrowsingProvider
from app.schemas.threat_intel import Verdict

# 1. Test URL Normalization & Privacy Stripping
def test_safe_browsing_url_normalization():
    service = SafeBrowsingService()
    # Test basic trimming and lowercasing
    raw1 = "  HTTPS://EXAMPLE.COM/Path/Login?User=Admin&token=123  "
    norm1 = service.normalize_url(raw1)
    assert norm1.startswith("https://example.com/Path/Login?User=Admin&token=123")
    
    # Test stripping embedded basic-auth user:pass
    raw2 = "http://victim:secretpassword@malicious-phishing.top/verify"
    norm2 = service.normalize_url(raw2)
    assert "secretpassword" not in norm2
    assert "victim" not in norm2
    assert "malicious-phishing.top" in norm2

# 2. Test Clean URL Check (Mocked Google API Response)
@pytest.mark.asyncio
async def test_safe_browsing_clean_url():
    service = SafeBrowsingService()
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"matches": []}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        
        result = await service.check_url("https://clean-site.org/home")
        assert result.checked is True
        assert result.safe is True
        assert result.threat_detected is False
        assert result.threat_types == []
        assert result.error is None

# 3. Test Malicious/Phishing URL Detection (Mocked Threat Match)
@pytest.mark.asyncio
async def test_safe_browsing_threat_detected():
    service = SafeBrowsingService()
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "matches": [
            {
                "threatType": "SOCIAL_ENGINEERING",
                "platformType": "ANY_PLATFORM",
                "threatEntryType": "URL",
                "threat": {"url": "http://malicious-login.top/auth"},
                "cacheDuration": "300s"
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        
        result = await service.check_url("http://malicious-login.top/auth")
        assert result.checked is True
        assert result.safe is False
        assert result.threat_detected is True
        assert "SOCIAL_ENGINEERING" in result.threat_types
        assert result.source == "google_safe_browsing"

# 4. Test Multiple URLs Batch Evaluation & Deduplication
@pytest.mark.asyncio
async def test_safe_browsing_multiple_and_duplicate_urls():
    service = SafeBrowsingService()
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"matches": []}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        
        urls = [
            "https://site-a.com/page1",
            "https://site-b.com/page2",
            "https://site-a.com/page1",  # Duplicate
            "  HTTPS://SITE-A.COM/page1  "  # Normalized Duplicate
        ]
        
        results = await service.check_urls(urls)
        assert len(results) == 2  # Deduplicated into 2 unique URLs

# 5. Test Missing API Key Handling
@pytest.mark.asyncio
async def test_safe_browsing_missing_api_key():
    service = SafeBrowsingService()
    with patch.object(service, "_get_api_key", return_value=""):
        result = await service.check_url("https://example.com/test")
        assert result.checked is False
        assert result.error == "not_configured"

# 6. Test Invalid API Key / Blocked API Key (HTTP 400/403)
@pytest.mark.asyncio
async def test_safe_browsing_blocked_or_invalid_key():
    service = SafeBrowsingService()
    
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "API_KEY_SERVICE_BLOCKED"
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        
        result = await service.check_url("https://example.com/test")
        assert result.checked is False
        assert result.error == "api_key_service_blocked"

# 7. Test Rate Limit Response (HTTP 429)
@pytest.mark.asyncio
async def test_safe_browsing_rate_limited():
    service = SafeBrowsingService()
    
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        
        result = await service.check_url("https://example.com/test")
        assert result.checked is False
        assert result.error == "rate_limited"

# 8. Test Timeout Handling
@pytest.mark.asyncio
async def test_safe_browsing_timeout():
    service = SafeBrowsingService()
    import httpx
    
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        result = await service.check_url("https://example.com/test")
        assert result.checked is False
        assert result.error == "timeout"

# 9. Test GoogleSafeBrowsingProvider Integration
@pytest.mark.asyncio
async def test_google_safe_browsing_provider():
    provider = GoogleSafeBrowsingProvider()
    
    mock_sb_result = SafeBrowsingResult(
        url="http://test-phish.click",
        normalized_url="http://test-phish.click",
        checked=True,
        safe=False,
        threat_detected=True,
        threat_types=["SOCIAL_ENGINEERING", "MALWARE"],
        platform_types=["ANY_PLATFORM"],
        error=None
    )
    
    with patch("app.services.safe_browsing.safe_browsing_service.check_url", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = mock_sb_result
        
        res = await provider.lookup("http://test-phish.click", "URL")
        assert res.provider == "GoogleSafeBrowsing"
        assert res.verdict == Verdict.MALICIOUS
        assert res.confidence >= 0.90
        assert "SOCIAL_ENGINEERING" in res.categories
        assert any("Google Safe Browsing match" in e for e in res.evidence)

# 10. Test Safe Browsing Health Check
@pytest.mark.asyncio
async def test_safe_browsing_health_check():
    service = SafeBrowsingService()
    health = await service.health_check()
    assert health["provider"] == "GoogleSafeBrowsing"
    assert "configured" in health
    assert "status" in health
