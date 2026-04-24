"""Real-time notifications via WebSocket + Redis pub/sub."""
from __future__ import annotations

import asyncio
import json

import redis.asyncio as aioredis
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.config import settings
from app.core.logging import logger
from app.core.security import decode_token

router = APIRouter(prefix="/ws", tags=["websocket"])

PING_INTERVAL = 30


@router.websocket("/notifications")
async def notifications_ws(websocket: WebSocket, token: str = Query(...)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    await websocket.accept()
    logger.info("ws_notifications_connected", user_id=user_id)

    redis_client: aioredis.Redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis_client.pubsub()

    try:
        await pubsub.subscribe("notifications")

        async def redis_listener():
            async for raw in pubsub.listen():
                if raw["type"] == "message":
                    await websocket.send_text(raw["data"])

        listener_task = asyncio.create_task(redis_listener())

        try:
            while True:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=PING_INTERVAL)
                except asyncio.TimeoutError:
                    await websocket.send_text(json.dumps({"type": "ping"}))
        except WebSocketDisconnect:
            logger.info("ws_notifications_disconnected", user_id=user_id)
        finally:
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

    except Exception as exc:
        logger.error("ws_notifications_error", user_id=user_id, error=str(exc))
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        await pubsub.unsubscribe("notifications")
        await pubsub.aclose()
        await redis_client.aclose()
