import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.engine.tempmail_ingestion import TempMailIngestionService
from app.agents.attachment_agent import AttachmentAnalysisAgent
from app.models.agent import AgentRun
from app.models.investigation import Investigation, InputType, InvestigationStatus
from app.models.tempmail import TempMailMessage

# 1. Test Mailbox Validation
def test_mailbox_validation_syntax():
    valid_res = TempMailIngestionService.validate_mailbox("honeypot-alert@tempmail.so")
    assert valid_res["valid"] is True
    assert valid_res["status"] == "VALID"
    assert valid_res["domain"] == "tempmail.so"

    invalid_missing_at = TempMailIngestionService.validate_mailbox("invalidemail.com")
    assert invalid_missing_at["valid"] is False
    assert invalid_missing_at["status"] == "INVALID"

    invalid_chars = TempMailIngestionService.validate_mailbox("bad email!@domain.com")
    assert invalid_chars["valid"] is False

# 2. Test Safe Attachment Analysis Agent (Zero Host Execution)
@pytest.mark.asyncio
async def test_attachment_analysis_agent_clean():
    inv_id = "test-inv-att-clean"
    mock_session = AsyncMock()
    
    mock_inv = Investigation(
        id=inv_id,
        display_id="INV-2026-CLEAN",
        input_type=InputType.EMAIL,
        target="Subject: Clean email",
        status=InvestigationStatus.INITIAL_ANALYSIS
    )
    mock_session.get.return_value = mock_inv
    
    # Mock no TempMailMessage attachment
    mock_msg_res = MagicMock()
    mock_msg_res.scalar_one_or_none.return_value = None
    
    # Mock no Artifacts
    mock_art_res = MagicMock()
    mock_art_res.scalars.return_value.all.return_value = []
    
    mock_session.execute.side_effect = [mock_msg_res, mock_art_res]
    
    run = AgentRun(id="run-1", investigation_id=inv_id, agent_name="attachment_analysis", status="RUNNING")
    
    result = await AttachmentAnalysisAgent._execute(inv_id, mock_session, run)
    assert result.status == "COMPLETED"
    assert len(result.findings) >= 1
    assert result.findings[0]["category"] == "attachment_security"
    assert "No Suspicious Attachments" in result.findings[0]["title"]

@pytest.mark.asyncio
async def test_attachment_analysis_agent_dangerous_payload():
    inv_id = "test-inv-att-danger"
    mock_session = AsyncMock()
    
    mock_inv = Investigation(
        id=inv_id,
        display_id="INV-2026-MALWARE",
        input_type=InputType.EMAIL,
        target="Subject: Invoice attached",
        status=InvestigationStatus.INITIAL_ANALYSIS
    )
    mock_session.get.return_value = mock_inv
    
    # Mock malicious .exe attachment in message
    mock_msg = TempMailMessage(
        inbox_id="ib-1",
        provider_message_id="msg-malware",
        attachment_metadata=[{
            "filename": "urgent_payment_remittance.exe",
            "mime_type": "application/x-msdownload",
            "size": 1048576,
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }]
    )
    mock_msg_res = MagicMock()
    mock_msg_res.scalar_one_or_none.return_value = mock_msg
    
    mock_art_res = MagicMock()
    mock_art_res.scalars.return_value.all.return_value = []
    mock_session.execute.side_effect = [mock_msg_res, mock_art_res]
    
    run = AgentRun(id="run-2", investigation_id=inv_id, agent_name="attachment_analysis", status="RUNNING")
    
    result = await AttachmentAnalysisAgent._execute(inv_id, mock_session, run)
    assert result.status == "COMPLETED"
    assert len(result.findings) >= 1
    assert result.findings[0]["category"] == "malware_payload"
    assert result.findings[0]["severity"] == "critical"
    assert "Executable Attachment" in result.findings[0]["title"]
