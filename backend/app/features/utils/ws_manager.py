import asyncio
import json
from fastapi import WebSocket
from core.database.redis.redis_utils import get_redis_client


class QuizConnectionManager:
    """WS rooms fed by Redis pub/sub. Room is a string: "global" or a quiz id."""

    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = {}
        self._started = False

    async def connect(self, room: str, ws: WebSocket):
        await ws.accept()
        self._rooms.setdefault(room, set()).add(ws)
        if not self._started:
            asyncio.create_task(self._listen())
            self._started = True

    def disconnect(self, room: str, ws: WebSocket):
        conns = self._rooms.get(room)
        if conns:
            conns.discard(ws)
            if not conns:
                del self._rooms[room]

    async def _broadcast(self, room: str, event: dict):
        dead = []
        for ws in self._rooms.get(room, set()):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(room, ws)

    async def _listen(self):
        pubsub = get_redis_client().pubsub()
        pubsub.psubscribe("quiz:*:events")
        while True:
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if msg and msg["type"] == "pmessage":
                room = msg["channel"].split(":")[1]  # "global" or quiz id
                await self._broadcast(room, json.loads(msg["data"]))
            await asyncio.sleep(0.05)


quiz_ws_manager = QuizConnectionManager()
