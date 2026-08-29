import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime, timezone
from fastapi import WebSocket
from ..schemas.agent_event import AgentEvent

logger = logging.getLogger("event_broadcaster")

class EventBroadcaster:
    """
    Central Real-Time Multi-Agent Event Broadcaster.
    Maintains active WebSocket and Server-Sent Event (SSE) subscribers per investigation.
    Ensures zero-latency delivery of live agent decisions, tool calls, and risk updates.
    """
    def __init__(self):
        # Maps investigation_id -> Set of active WebSocket connections
        self._ws_subscribers: Dict[str, Set[WebSocket]] = {}
        # Maps investigation_id -> List of asyncio.Queue for SSE streams
        self._sse_subscribers: Dict[str, List[asyncio.Queue]] = {}
        # In-memory recent event buffer per investigation for fast replay
        self._event_buffer: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def register_ws(self, investigation_id: str, websocket: WebSocket):
        """Registers a new WebSocket subscriber for an investigation."""
        async with self._lock:
            if investigation_id not in self._ws_subscribers:
                self._ws_subscribers[investigation_id] = set()
            self._ws_subscribers[investigation_id].add(websocket)
        logger.info(f"WebSocket registered for investigation {investigation_id} (Total: {len(self._ws_subscribers[investigation_id])})")

    async def unregister_ws(self, investigation_id: str, websocket: WebSocket):
        """Unregisters a WebSocket subscriber."""
        async with self._lock:
            if investigation_id in self._ws_subscribers:
                self._ws_subscribers[investigation_id].discard(websocket)
                if not self._ws_subscribers[investigation_id]:
                    del self._ws_subscribers[investigation_id]

    async def subscribe_sse(self, investigation_id: str) -> asyncio.Queue:
        """Registers a new SSE listener queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            if investigation_id not in self._sse_subscribers:
                self._sse_subscribers[investigation_id] = []
            self._sse_subscribers[investigation_id].append(queue)
        return queue

    async def unsubscribe_sse(self, investigation_id: str, queue: asyncio.Queue):
        """Unregisters an SSE listener queue."""
        async with self._lock:
            if investigation_id in self._sse_subscribers:
                if queue in self._sse_subscribers[investigation_id]:
                    self._sse_subscribers[investigation_id].remove(queue)
                if not self._sse_subscribers[investigation_id]:
                    del self._sse_subscribers[investigation_id]

    def get_buffered_events(self, investigation_id: str) -> List[Dict[str, Any]]:
        """Returns in-memory buffered events for fast hydration."""
        return self._event_buffer.get(investigation_id, [])

    async def emit(self, event: AgentEvent, persist: bool = True):
        """
        Emits an agent event to all active WebSocket and SSE clients,
        buffers the event in memory, and persists to PostgreSQL.
        """
        payload = event.model_dump(mode='json')
        inv_id = event.investigation_id

        # 1. Update in-memory buffer
        if inv_id not in self._event_buffer:
            self._event_buffer[inv_id] = []
        self._event_buffer[inv_id].append(payload)
        # Cap buffer at 200 events per investigation
        if len(self._event_buffer[inv_id]) > 200:
            self._event_buffer[inv_id] = self._event_buffer[inv_id][-200:]

        # 2. Broadcast to WebSockets
        dead_ws = set()
        ws_list = list(self._ws_subscribers.get(inv_id, set()))
        for ws in ws_list:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead_ws.add(ws)

        if dead_ws:
            async with self._lock:
                for ws in dead_ws:
                    self._ws_subscribers[inv_id].discard(ws)

        # 3. Broadcast to SSE queues
        sse_queues = list(self._sse_subscribers.get(inv_id, []))
        for q in sse_queues:
            try:
                if q.full():
                    try:
                        q.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await q.put(payload)
            except Exception:
                pass

        # 4. Async persistence in database
        if persist:
            try:
                from ..database.connection import AsyncSessionLocal
                from ..models.event import InvestigationEvent
                
                async with AsyncSessionLocal() as session:
                    db_event = InvestigationEvent(
                        investigation_id=inv_id,
                        event_type=event.event_type,
                        source=event.agent_name or event.agent_id,
                        severity=event.data.get("severity", "INFO"),
                        metadata_payload={
                            "agent_id": event.agent_id,
                            "agent_name": event.agent_name,
                            "status": event.status,
                            "message": event.message,
                            "data": event.data,
                            "timestamp": event.timestamp
                        }
                    )
                    session.add(db_event)
                    await session.commit()
            except Exception as dbe:
                logger.debug(f"Event persistence notice: {dbe}")

# Global singleton event broadcaster
event_broadcaster = EventBroadcaster()
