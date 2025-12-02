"""WebSocket support for real-time updates."""

import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()


async def broadcast_job_update(message: dict):
    """Broadcast job update to all connected clients."""
    if not active_connections:
        return

    message_json = json.dumps(message)
    disconnected = set()

    for connection in active_connections:
        try:
            await connection.send_text(message_json)
        except Exception as e:
            logger.warning(f"Failed to send message to WebSocket client: {e}")
            disconnected.add(connection)

    # Remove disconnected clients
    active_connections.difference_update(disconnected)


@router.websocket("/ws/scheduler")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time scheduler updates."""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")

    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_text(json.dumps({"type": "pong", "message": "Connection active"}))
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        active_connections.discard(websocket)
