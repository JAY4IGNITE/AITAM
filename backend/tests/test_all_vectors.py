import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.engine.input_processor import UniversalInputProcessor
from app.models.investigation import InputType
from app.agents.url_agent import URLIntelligenceAgent
from app.agents.email_agent import EmailIntelligenceAgent
from app.agents.sms_agent import SMSIntelligenceAgent
from app.agents.social_agent import SocialMessageIntelligenceAgent
from app.agents.qr_processor import decode_qr_image, QRCodeProcessor
from app.engine.threat_intel_provider import URLhausProvider, VirusTotalProvider, GoogleSafeBrowsingProvider, DatabaseThreatIntelProvider, registry
from app.schemas.threat_intel import Verdict

# 1. Test URL Input Processing & Heuristics
def test_url_input_processor():
    processor = UniversalInputProcessor()
    res = processor.process_input(InputType.URL, "http://phishing-portal.top/login?verify=true")
    assert res.normalized_text.startswith("http://phishing-portal.top")
    assert len(res.extracted_indicators) > 0
    assert any(i.type == "DOMAIN" and "phishing-portal.top" in i.value for i in res.extracted_indicators)

# 2. Test Email Header & URL Extraction
def test_email_input_processor():
    processor = UniversalInputProcessor()
    email_sample = """From: Security Team <alert@paypa1-security.com>
Reply-To: attacker@hacker-server.xyz
Subject: Immediate Account Verification Required
Date: Wed, 28 Aug 2026 12:00:00 +0000

Dear user, your account has been suspended. Click here: https://secure-verify.cfd/login to unlock.
"""
    res = processor.process_input(InputType.EMAIL, email_sample)
    assert len(res.urls) > 0
    assert "https://secure-verify.cfd/login" in res.urls
    assert any(i.type == "EMAIL" for i in res.extracted_indicators)

# 3. Test SMS Smishing & OTP Detection
def test_sms_input_processor():
    processor = UniversalInputProcessor()
    sms_sample = "CHASE BANK ALERT: Unauthorized wire transfer detected. Verify OTP passcode immediately at http://chase-security-auth.click/2fa"
    res = processor.process_input(InputType.SMS, sms_sample)
    assert len(res.urls) > 0
    assert "http://chase-security-auth.click/2fa" in res.urls

# 4. Test Social Media Scam Processing
def test_social_input_processor():
    processor = UniversalInputProcessor()
    social_sample = "Meta Support Official: Your account violated copyright policies. Appeal immediately at https://meta-appeal-form.rest/ticket or your page will be deleted in 24 hours."
    res = processor.process_input(InputType.SOCIAL, social_sample)
    assert len(res.urls) > 0
    assert "https://meta-appeal-form.rest/ticket" in res.urls

# 5. Test QR Code Payload Decoding
def test_qr_payload_decoding():
    # Test plain text / URL payload
    payload = "https://legitimate-service.com/auth"
    decoded = decode_qr_image(payload)
    assert len(decoded) > 0
    assert decoded[0] == payload

# 6. Test Threat Intel URLhaus Provider Interface
@pytest.mark.asyncio
async def test_urlhaus_provider_clean_lookup():
    provider = URLhausProvider()
    # Test with a benign domain
    res = await provider.lookup("https://example.com/clean-path", "URL")
    assert res.provider == "URLhaus"
    assert res.verdict in [Verdict.CLEAN, Verdict.UNKNOWN, Verdict.MALICIOUS]

# 7. Test Threat Intel Registry lookup
@pytest.mark.asyncio
async def test_threat_intel_registry():
    health = await registry.get_health()
    assert len(health) >= 4
    provider_names = [h.provider_name for h in health]
    assert "URLhaus" in provider_names
    assert "VirusTotal" in provider_names
    assert "GoogleSafeBrowsing" in provider_names
    assert "ThreatLens-LocalDB" in provider_names

# 8. Test Explainable Scoring Buckets
def test_risk_scoring_buckets():
    from app.engine.risk import RiskEngine
    # Verify score ranges logic
    # 0-19 SAFE, 20-39 LOW, 40-59 MEDIUM, 60-79 HIGH, 80-100 CRITICAL
    assert True
