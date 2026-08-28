from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, investigation_id: str):
        await websocket.accept()
        if investigation_id not in self.active_connections:
            self.active_connections[investigation_id] = []
        self.active_connections[investigation_id].append(websocket)

    def disconnect(self, websocket: WebSocket, investigation_id: str):
        if investigation_id in self.active_connections:
            self.active_connections[investigation_id].remove(websocket)

    async def broadcast(self, investigation_id: str, message: dict):
        if investigation_id in self.active_connections:
            for connection in self.active_connections[investigation_id]:
                await connection.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/investigations/{investigation_id}")
async def websocket_endpoint(websocket: WebSocket, investigation_id: str):
    await manager.connect(websocket, investigation_id)
    try:
        while True:
            # We don't really expect client to send messages, just listen
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, investigation_id)
