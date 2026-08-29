from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

class AgentEvent(BaseModel):
    """
    Standardized Real-Time Agent Execution Event.
    Emitted whenever an agent starts, reasons, invokes a tool, creates evidence, or completes.
    """
    investigation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_id: str
    agent_name: str
    event_type: str  # agent_started, agent_thinking, tool_started, tool_completed, agent_message, agent_completed, agent_failed, evidence_created, risk_updated, investigation_completed
    status: str = "RUNNING"  # IDLE, QUEUED, RUNNING, WAITING, COMPLETED, FAILED
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
