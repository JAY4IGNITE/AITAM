import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
from app.schemas.agent_event import AgentEvent
from app.engine.event_broadcaster import event_broadcaster, EventBroadcaster
from app.services.safe_browsing import SafeBrowsingService

# 1. Test Event Broadcaster In-Memory Buffering & Emitting
@pytest.mark.asyncio
async def test_event_broadcaster_emission():
    broadcaster = EventBroadcaster()
    inv_id = "test-inv-12345"
    
    event = AgentEvent(
        investigation_id=inv_id,
        agent_id="url_intelligence",
        agent_name="URL Intelligence Agent",
        event_type="agent_started",
        status="RUNNING",
        message="Evaluating extracted indicators",
        data={"target": "https://test-phish.top/login"}
    )
    
    # Emit event without database persistence in unit test
    await broadcaster.emit(event, persist=False)
    
    buffered = broadcaster.get_buffered_events(inv_id)
    assert len(buffered) == 1
    assert buffered[0]["agent_id"] == "url_intelligence"
    assert buffered[0]["event_type"] == "agent_started"
    assert buffered[0]["status"] == "RUNNING"

# 2. Test SSE Subscription & Real-Time Queueing
@pytest.mark.asyncio
async def test_event_broadcaster_sse_subscription():
    broadcaster = EventBroadcaster()
    inv_id = "test-inv-sse-999"
    
    queue = await broadcaster.subscribe_sse(inv_id)
    assert queue is not None
    
    event = AgentEvent(
        investigation_id=inv_id,
        agent_id="triage_agent",
        agent_name="Triage Agent",
        event_type="agent_completed",
        status="COMPLETED",
        message="Triage priority assigned: P1_CRITICAL",
        data={"priority": "P1_CRITICAL"}
    )
    
    await broadcaster.emit(event, persist=False)
    
    # Verify received item in queue
    received = await asyncio.wait_for(queue.get(), timeout=2.0)
    assert received["agent_id"] == "triage_agent"
    assert received["status"] == "COMPLETED"
    assert received["data"]["priority"] == "P1_CRITICAL"
    
    await broadcaster.unsubscribe_sse(inv_id, queue)

# 3. Test Safe Browsing Tool Event Emission
@pytest.mark.asyncio
async def test_safe_browsing_tool_event_emission():
    service = SafeBrowsingService()
    inv_id = "test-inv-sb-tool"
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "matches": [{
            "threatType": "SOCIAL_ENGINEERING",
            "platformType": "ANY_PLATFORM"
        }]
    }
    
    with patch("app.engine.event_broadcaster.EventBroadcaster.emit", new_callable=AsyncMock) as mock_emit:
        with patch.object(service, "_get_api_key", return_value="fake_key"):
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_resp
                
                res = await service.check_url("http://phish.top/login", investigation_id=inv_id)
                assert res.threat_detected is True
                
                # Check that tool events were emitted
                assert mock_emit.call_count >= 2
