from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.ws_manager import manager
from app.auth import decode_token

router = APIRouter()


@router.websocket("/ws/boards/{board_id}")
async def board_socket(websocket: WebSocket, board_id: str, token: str = Query(...)):
    payload = decode_token(token)
    if payload is None:
        await websocket.close(code=4401)
        return

    await manager.connect(board_id, websocket)
    try:
        while True:
            # We don't expect inbound messages beyond keepalive pings;
            # all state changes go through the REST API, which broadcasts.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(board_id, websocket)
