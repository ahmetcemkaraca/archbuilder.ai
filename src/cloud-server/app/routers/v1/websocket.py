from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(prefix="/v1/ws", tags=["websocket"])


@router.websocket("")
async def ws_endpoint(websocket: WebSocket, correlation_id: str) -> None:
    await websocket.accept()
    try:
        # TR: Basit hoş geldin ve ping-pong mekanizması
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "correlationId": correlation_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "payload": {"message": "Connected"},
                }
            )
        )

        while True:
            _ = await websocket.receive_text()
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "pong",
                        "correlationId": correlation_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "payload": {},
                    }
                )
            )
    except WebSocketDisconnect:
        return
