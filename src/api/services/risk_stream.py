from __future__ import annotations

from datetime import UTC, datetime

from src.api.services.risk import RiskAnalyticsService
from src.api.websocket import ConnectionManager, risk_connection_manager


class RiskStreamService:
    """Publish graph-grounded company risk updates to WebSocket clients."""

    def __init__(
        self,
        risk_service: RiskAnalyticsService,
        *,
        manager: ConnectionManager = risk_connection_manager,
    ) -> None:
        self.risk_service = risk_service
        self.manager = manager

    async def publish_company_risk(
        self,
        *,
        company_id: str,
        event_id: str | None = None,
        event_type: str | None = None,
        max_hops: int = 3,
    ) -> dict:
        risk = self.risk_service.get_company_risk(
            company_id,
            max_hops=max_hops,
        )

        message = {
            "type": "risk.updated",
            "event_id": event_id,
            "company_id": risk["company_id"],
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "contributing_event_count": risk["contributing_event_count"],
            "max_hops": risk["max_hops"],
            "trigger_event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        await self.manager.broadcast(message)
        return message
