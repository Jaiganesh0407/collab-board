import json
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Tracks active WebSocket connections per board and broadcasts events."""

    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, board_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active.setdefault(board_id, []).append(websocket)

    def disconnect(self, board_id: str, websocket: WebSocket):
        if board_id in self.active and websocket in self.active[board_id]:
            self.active[board_id].remove(websocket)
            if not self.active[board_id]:
                del self.active[board_id]

    async def broadcast(self, board_id: str, message: dict, exclude: WebSocket = None):
        for connection in self.active.get(board_id, []):
            if connection is exclude:
                continue
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass


manager = ConnectionManager()
