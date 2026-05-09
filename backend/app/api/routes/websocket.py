"""
WebSocket endpoint — bridges Redis Pub/Sub to connected browser clients.

Architecture:
  Workers → Redis Pub/Sub → This endpoint → WebSocket → Browser

Features:
  - Heartbeat / ping-pong to detect stale connections
  - Reconnect-friendly (clients can re-subscribe on reconnect)
  - Symbol-level subscriptions (watchlist filtering)
  - Message versioning for schema evolution
  - Deduplication via event_id tracking (per-connection)
"""
import asyncio
import json
import time
from typing import Set

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.realtime.redis_client import get_redis_client

router = APIRouter()
log = structlog.get_logger()

HEARTBEAT_INTERVAL = 15  # seconds
SUBSCRIBE_CHANNELS = [
    "stock_intel:news:ALL",
    "stock_intel:analyst:ALL",
    "stock_intel:insider:ALL",
    "stock_intel:price:ALL",
    "stock_intel:score:ALL",
]


@router.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    symbols: str = Query(default=""),  # comma-separated watchlist filter
):
    """
    WebSocket endpoint for real-time event streaming.

    Query params:
      symbols: optional comma-separated list to filter by watchlist
               if empty, all symbols are forwarded

    Message format (JSON):
      {
        "v": 1,               // message schema version
        "type": "news|analyst|insider|price|score|heartbeat|error",
        "symbol": "NVDA",
        "freshness_tier": "POLLED|NEAR_REALTIME|FILING_DELAYED|STREAMING",
        "event_timestamp": "ISO-8601",
        "...": "...type-specific fields"
      }
    """
    await websocket.accept()
    client_id = id(websocket)
    symbol_filter: Set[str] = set(s.strip().upper() for s in symbols.split(",") if s.strip())
    seen_event_ids: Set[str] = set()

    log.info("ws.connected", client=client_id, filter=symbol_filter or "ALL")

    redis = await get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.subscribe(*SUBSCRIBE_CHANNELS)

    # Add per-symbol channels if filter is active
    if symbol_filter:
        extra_channels = []
        for sym in symbol_filter:
            extra_channels.extend([
                f"stock_intel:news:{sym}",
                f"stock_intel:analyst:{sym}",
                f"stock_intel:insider:{sym}",
                f"stock_intel:score:{sym}",
            ])
        await pubsub.subscribe(*extra_channels)

    async def send_heartbeat():
        while True:
            try:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await websocket.send_json({
                    "v": 1,
                    "type": "heartbeat",
                    "ts": time.time(),
                })
            except Exception:
                break

    async def forward_redis_messages():
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                data = json.loads(message["data"])
                data["v"] = 1  # add schema version

                # Deduplication
                event_id = f"{data.get('type')}:{data.get('symbol')}:{data.get('event_timestamp')}"
                if event_id in seen_event_ids:
                    continue
                seen_event_ids.add(event_id)
                # Prevent unbounded growth
                if len(seen_event_ids) > 1000:
                    seen_event_ids.clear()

                # Symbol filter
                sym = data.get("symbol", "")
                if symbol_filter and sym not in symbol_filter:
                    continue

                await websocket.send_json(data)
            except Exception as e:
                log.warning("ws.forward_error", error=str(e))

    try:
        await asyncio.gather(
            send_heartbeat(),
            forward_redis_messages(),
        )
    except (WebSocketDisconnect, asyncio.CancelledError):
        log.info("ws.disconnected", client=client_id)
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()
