from __future__ import annotations

import logging
from typing import Any

from fastapi import WebSocket


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage active risk-stream WebSocket clients."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "Risk WebSocket connected active_connections=%d",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            "Risk WebSocket disconnected active_connections=%d",
            len(self.active_connections),
        )

    async def send_json(
        self,
        websocket: WebSocket,
        message: dict[str, Any],
    ) -> None:
        await websocket.send_json(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                logger.exception("Failed to send WebSocket risk update.")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


risk_connection_manager = ConnectionManager()
