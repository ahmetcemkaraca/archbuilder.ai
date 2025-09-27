from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Any

from fastapi import WebSocket


class WebSocketManager:
    """Basit korelasyon-id tabanlı WS bağlantı yöneticisi.

    TR: Üretimde Redis veya dağıtık bir katman tercih edilmeli; burada
    tek-nod hafif kullanım içindir.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, correlation_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[correlation_id] = websocket
        await self.send(
            correlation_id,
            {
                "type": "connection_established",
                "correlationId": correlation_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "payload": {"message": "Connected"},
            },
        )

    async def disconnect(self, correlation_id: str) -> None:
        self._connections.pop(correlation_id, None)

    async def send(self, correlation_id: str, message: Dict[str, Any]) -> None:
        ws = self._connections.get(correlation_id)
        if not ws:
            return
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            await self.disconnect(correlation_id)

    async def broadcast_progress(
        self,
        correlation_id: str,
        stage: str,
        progress: float,
        message: str | None = None,
    ) -> None:
        await self.send(
            correlation_id,
            {
                "type": "progress_update",
                "correlationId": correlation_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "payload": {
                    "stage": stage,
                    "progress": progress,
                    "message": message or f"Processing: {stage}",
                },
            },
        )


# TR: İsteğe bağlı tekil örnek
ws_manager = WebSocketManager()
