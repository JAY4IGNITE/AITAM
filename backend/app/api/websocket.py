from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from ..engine.event_broadcaster import event_broadcaster

logger = logging.getLogger("websocket")
router = APIRouter()

@router.websocket("/ws/investigations/{investigation_id}")
async def websocket_investigation_endpoint(websocket: WebSocket, investigation_id: str):
    await websocket.accept()
    await event_broadcaster.register_ws(investigation_id, websocket)
    
    # 1. Immediately hydrate client with recent buffered events
    try:
        buffered = event_broadcaster.get_buffered_events(investigation_id)
        if buffered:
            for ev in buffered:
                await websocket.send_text(json.dumps(ev))
    except Exception as e:
        logger.debug(f"Hydration notice: {e}")

    # 2. Listen for client pings or disconnects
    try:
        while True:
            msg = await websocket.receive_text()
            # Respond to client ping with pong heartbeat
            if msg == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "investigation_id": investigation_id}))
    except WebSocketDisconnect:
        await event_broadcaster.unregister_ws(investigation_id, websocket)
    except Exception as ex:
        await event_broadcaster.unregister_ws(investigation_id, websocket)
