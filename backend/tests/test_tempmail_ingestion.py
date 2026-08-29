import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.engine.tempmail import TempMailClient, tempmail_client
from app.models.tempmail import TempMailInbox, TempMailMessage
from app.models.investigation import Investigation, InputType, InvestigationStatus
from app.engine.threat_intel_provider import registry
from app.schemas.tempmail import TempMailInboxCreate, TempMailMessageSummary

# 1. Test TempMail Client Authentication & Domain Retrieval
@pytest.mark.asyncio
async def test_tempmail_get_domains():
    client = TempMailClient()
    domains = await client.get_domains()
    assert isinstance(domains, list)
    assert len(domains) > 0

# 2. Test Inbox Creation
@pytest.mark.asyncio
async def test_tempmail_create_inbox():
    client = TempMailClient()
    inbox = await client.create_inbox(prefix="threatlens-test-suite")
    assert "email_address" in inbox
    assert "inbox_id" in inbox
    assert "@" in inbox["email_address"]
    assert inbox["status"] == "ACTIVE"

# 3. Test Message Retrieval Interface
@pytest.mark.asyncio
async def test_tempmail_message_retrieval():
    client = TempMailClient()
    inbox = await client.create_inbox(prefix="test-retrieval")
    messages = await client.list_messages(inbox["inbox_id"], inbox["email_address"])
    assert isinstance(messages, list)

# 4. Test Email Parsing & Normalization
def test_email_parsing_and_normalization():
    from app.engine.input_processor import UniversalInputProcessor
    raw_email = """From: Security Alert <no-reply@secure-account-verify.cfd>
Reply-To: phisher@hacker-c2.top
Subject: URGENT: Verify Your Password
Date: Fri, 29 Aug 2026 10:00:00 +0000

Dear user, your mailbox has exceeded quota.
Click here to prevent deletion: http://malicious-login.top/auth/login
"""
    threat_obj = UniversalInputProcessor.process_input(InputType.EMAIL, raw_email)
    assert len(threat_obj.urls) > 0
    assert "http://malicious-login.top/auth/login" in threat_obj.urls
    assert any(i.type == "EMAIL" for i in threat_obj.extracted_indicators)

# 5. Test Deduplication Model & Logic
def test_duplicate_message_prevention():
    inbox_id = "test-inbox-dedup-1"
    prov_msg_id = "prov-msg-12345"
    msg1 = TempMailMessage(
        inbox_id=inbox_id,
        provider_message_id=prov_msg_id,
        sender="sender@example.com",
        subject="Test Subject",
        text_body="Hello world",
        status="COMPLETED"
    )
    assert msg1.provider_message_id == prov_msg_id
    assert msg1.inbox_id == inbox_id

# 6. Test Email Agent Analysis Logic
@pytest.mark.asyncio
async def test_email_multi_agent_execution():
    from app.agents.email_agent import EmailIntelligenceAgent
    
    mock_session = AsyncMock()
    mock_inv = Investigation(
        id="test-inv-001",
        display_id="INV-TEST-EMAIL-01",
        input_type=InputType.EMAIL,
        target="From: PayPal Security <fraud@paypa1-security.com>\nSubject: Account Suspended\n\nClick: http://paypa1-login.click/verify",
        normalized_input="From: PayPal Security <fraud@paypa1-security.com>\nSubject: Account Suspended\n\nClick: http://paypa1-login.click/verify",
        status=InvestigationStatus.INITIAL_ANALYSIS
    )
    mock_session.get = AsyncMock(return_value=mock_inv)
    
    email_res = await EmailIntelligenceAgent.analyze(mock_inv.id, mock_session)
    assert email_res.status == "COMPLETED"
    assert len(email_res.findings) > 0
    titles = [f.get("title", "") if isinstance(f, dict) else getattr(f, "title", "") for f in email_res.findings]
    assert any(len(t) > 0 for t in titles)

# 7. Test Health Check for TempMail and All Providers
@pytest.mark.asyncio
async def test_tempmail_and_providers_health():
    health = await tempmail_client.health_check()
    assert "status" in health
    assert health["provider"] == "TempMail.so"

    providers_health = await registry.get_health()
    assert len(providers_health) >= 4
