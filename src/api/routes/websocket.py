from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.websocket import risk_connection_manager


router = APIRouter(tags=["websocket"])


@router.websocket("/risk-stream")
async def risk_stream(websocket: WebSocket) -> None:
    await risk_connection_manager.connect(websocket)

    try:
        await risk_connection_manager.send_json(
            websocket,
            {
                "type": "connection.established",
                "message": "Connected to supply-chain risk stream.",
            },
        )

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        risk_connection_manager.disconnect(websocket)

    except Exception:
        risk_connection_manager.disconnect(websocket)
        raise
