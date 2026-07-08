from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from features.utils.ws_manager import quiz_ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/feed")
async def feed_ws(ws: WebSocket):
    await quiz_ws_manager.connect("global", ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        quiz_ws_manager.disconnect("global", ws)


@router.websocket("/ws/quiz/{quiz_id}")
async def quiz_ws(quiz_id: int, ws: WebSocket):
    room = str(quiz_id)
    await quiz_ws_manager.connect(room, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        quiz_ws_manager.disconnect(room, ws)
