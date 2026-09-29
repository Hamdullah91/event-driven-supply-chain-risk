from __future__ import annotations

import logging
from datetime import UTC, datetime

from src.api.services.risk import RiskAnalyticsService
from src.api.websocket import ConnectionManager, risk_connection_manager


logger = logging.getLogger(__name__)


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

    def impacted_company_ids_for_event(
        self,
        *,
        event_id: str,
        max_hops: int = 3,
    ) -> list[str]:
        """Return canonical company IDs whose risk can change for one Event.

        The authoritative Event blast-radius service already applies the same
        directed SUPPLIES traversal and supported hop boundary as production
        risk analytics. Reusing it keeps real-time invalidation scope aligned
        with risk propagation instead of relying only on directly linked
        Event companies.
        """
        if max_hops not in {1, 2, 3}:
            raise ValueError("max_hops must be between 1 and 3.")

        impact = self.risk_service.get_event_blast_radius(
            event_id,
            max_hops=max_hops,
        )
        return sorted(
            {
                str(company["company_id"])
                for company in impact.get("companies", [])
                if 0 <= int(company["hop_distance"]) <= max_hops
            }
        )

    async def publish_event_risk(
        self,
        *,
        event_id: str,
        event_type: str | None = None,
        max_hops: int = 3,
    ) -> list[dict]:
        """Publish one targeted update per Company affected within max_hops."""
        messages: list[dict] = []
        for company_id in self.impacted_company_ids_for_event(
            event_id=event_id,
            max_hops=max_hops,
        ):
            try:
                messages.append(
                    await self.publish_company_risk(
                        company_id=company_id,
                        event_id=event_id,
                        event_type=event_type,
                        max_hops=max_hops,
                    )
                )
            except Exception:
                # A single company update must not prevent publication for the
                # remaining affected companies or roll back an already-persisted
                # Event.
                logger.exception(
                    "Risk stream publish failed event_id=%s company_id=%s",
                    event_id,
                    company_id,
                )
        return messages

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
