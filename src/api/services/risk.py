from __future__ import annotations

from src.provenance import event_evidence_availability
from src.risk.aggregation import RiskContribution, aggregate_company_risk
from src.risk.mathematics import calculate_path_risk
from src.risk.repository import RiskRepository
from src.risk.scoring import severity_to_initial_risk


class RiskAnalyticsService:
    """Application service for graph-grounded risk analytics APIs."""

    def __init__(self, repository: RiskRepository) -> None:
        self.repository = repository

    def company_exists(self, company_id: str) -> bool:
        return self.repository.company_exists(company_id)

    def event_exists(self, event_id: str) -> bool:
        return self.repository.event_exists(event_id)

    @staticmethod
    def _path_risk(
        severity: str,
        hop_distance: int,
        weights: list[float],
    ) -> tuple[float, float, float, float]:
        initial_risk = severity_to_initial_risk(severity)
        if hop_distance == 0:
            return initial_risk, 1.0, 1.0, initial_risk
        result = calculate_path_risk(
            initial_risk=initial_risk,
            dependency_weights=weights,
        )
        return (
            initial_risk,
            result.path_dependency,
            result.distance_decay,
            result.propagated_risk,
        )

    def get_event_blast_radius(
        self,
        event_id: str,
        *,
        max_hops: int = 3,
    ) -> dict:
        rows = self.repository.get_event_blast_radius(
            event_id,
            max_hops=max_hops,
        )
        strongest_by_company: dict[str, dict] = {}
        event_type = None
        severity = None
        for row in rows:
            event_type = row.get("event_type")
            severity = str(row["severity"])
            hop = int(row["hop_distance"])
            weights = [
                float(weight)
                for weight in (row["dependency_weights"] or [])
            ]
            initial, dependency, decay, risk = self._path_risk(
                severity,
                hop,
                weights,
            )
            target = str(row["target_company_id"])
            candidate = {
                "company_id": target,
                "company_name": str(row["target_company_name"]),
                "origin_company_id": str(row["affected_company_id"]),
                "origin_company_name": str(row["affected_company_name"]),
                "hop_distance": hop,
                "initial_risk": initial,
                "path_dependency": dependency,
                "distance_decay": decay,
                "propagated_risk": risk,
                "path": list(row.get("path_nodes") or []),
            }
            if (
                target not in strongest_by_company
                or risk > strongest_by_company[target]["propagated_risk"]
            ):
                strongest_by_company[target] = candidate

        companies = sorted(
            strongest_by_company.values(),
            key=lambda item: (
                item["hop_distance"],
                -item["propagated_risk"],
                item["company_id"],
            ),
        )
        hop_counts = {
            str(hop): sum(
                1 for company in companies if company["hop_distance"] == hop
            )
            for hop in range(max_hops + 1)
        }
        return {
            "event_id": event_id,
            "event_type": event_type,
            "severity": severity,
            "max_hops": max_hops,
            "affected_company_count": len(companies),
            "hop_counts": hop_counts,
            "companies": companies,
        }

    def get_blast_radius(
        self,
        company_id: str,
        *,
        max_hops: int = 3,
    ) -> dict:
        rows = self.repository.get_company_blast_radius(
            company_id,
            max_hops=max_hops,
        )
        strongest: dict[str, dict] = {}
        for row in rows:
            weights = [
                float(item["dependency_weight"])
                for item in (row["path_relationships"] or [])
            ]
            result = calculate_path_risk(
                initial_risk=1.0,
                dependency_weights=weights,
            )
            target = str(row["target_company_id"])
            candidate = {
                "company_id": target,
                "company_name": str(row["target_company_name"]),
                "hop_distance": int(row["hop_distance"]),
                "transmission_factor": result.propagated_risk,
                "path": list(row["path_nodes"] or []),
            }
            if (
                target not in strongest
                or candidate["transmission_factor"]
                > strongest[target]["transmission_factor"]
            ):
                strongest[target] = candidate

        companies = sorted(
            strongest.values(),
            key=lambda item: (
                item["hop_distance"],
                -item["transmission_factor"],
                item["company_id"],
            ),
        )
        hops = {
            str(hop): sum(
                1 for company in companies if company["hop_distance"] == hop
            )
            for hop in range(1, max_hops + 1)
        }
        return {
            "company_id": company_id,
            "max_hops": max_hops,
            "affected_company_count": len(companies),
            "hop_counts": hops,
            "companies": companies,
        }

    def get_exposure(
        self,
        company_id: str,
        *,
        max_hops: int = 3,
    ) -> dict:
        rows = self.repository.get_company_event_exposure(
            company_id,
            max_hops=max_hops,
        )
        exposures: list[dict] = []
        for row in rows:
            severity = str(row["severity"])
            hop = int(row["hop_distance"])
            weights = [
                float(weight)
                for weight in (row["dependency_weights"] or [])
            ]
            initial, dependency, decay, risk = self._path_risk(
                severity,
                hop,
                weights,
            )
            evidence_properties = {
                "source": row.get("source"),
                "timestamp": row.get("timestamp"),
                "confidence": row.get("confidence"),
                "description": row.get("description"),
            }
            exposures.append(
                {
                    "event_id": str(row["event_id"]),
                    "event_type": row.get("event_type"),
                    "severity": severity,
                    "timestamp": row.get("timestamp"),
                    "source": row.get("source"),
                    "confidence": row.get("confidence"),
                    "description": row.get("description"),
                    "affected_company_id": str(row["affected_company_id"]),
                    "affected_company_name": str(row["affected_company_name"]),
                    "hop_distance": hop,
                    "initial_risk": initial,
                    "path_dependency": dependency,
                    "distance_decay": decay,
                    "propagated_risk": risk,
                    "path": list(row.get("path_nodes") or []),
                    "evidence_status": event_evidence_availability(
                        evidence_properties
                    ),
                }
            )
        exposures.sort(
            key=lambda item: (
                -item["propagated_risk"],
                item["hop_distance"],
                item["event_id"],
            )
        )
        return {
            "company_id": company_id,
            "event_count": len({item["event_id"] for item in exposures}),
            "exposures": exposures,
        }

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 0.75:
            return "CRITICAL"
        if score >= 0.50:
            return "HIGH"
        if score >= 0.25:
            return "MEDIUM"
        if score > 0:
            return "LOW"
        return "NONE"

    def get_company_risk(
        self,
        company_id: str,
        *,
        max_hops: int = 3,
    ) -> dict:
        exposure = self.get_exposure(company_id, max_hops=max_hops)
        strongest: dict[str, float] = {}
        for item in exposure["exposures"]:
            event_id = str(item["event_id"])
            strongest[event_id] = max(
                float(item["propagated_risk"]),
                strongest.get(event_id, 0.0),
            )
        aggregate = aggregate_company_risk(
            company_id=company_id,
            contributions=[
                RiskContribution(event_id=event_id, propagated_risk=risk)
                for event_id, risk in sorted(strongest.items())
            ],
        )
        score = aggregate.aggregate_risk
        return {
            "company_id": company_id,
            "risk_score": score,
            "risk_level": self._risk_level(score),
            "contributing_event_count": aggregate.event_count,
            "max_hops": max_hops,
        }

    def get_risk_history(
        self,
        company_id: str,
        *,
        max_hops: int = 3,
        limit: int = 100,
    ) -> dict:
        """Reconstruct one cumulative risk point per chronological event.

        The series is derived from timestamped graph event exposure, not from
        persisted wall-clock snapshots. When one event reaches the company via
        multiple paths, only that event's strongest propagated path contributes,
        matching current-risk aggregation semantics.
        """

        rows = list(
            self.repository.get_company_risk_history(
                company_id,
                max_hops=max_hops,
                limit=limit,
            )
        )

        strongest_by_event: dict[str, dict] = {}
        for row in rows:
            event_id = str(row["event_id"])
            severity = str(row["severity"])
            hop = int(row["hop_distance"])
            weights = [
                float(weight)
                for weight in (row["dependency_weights"] or [])
            ]
            _, _, _, risk = self._path_risk(severity, hop, weights)
            candidate = {
                "timestamp": row["timestamp"],
                "risk": risk,
            }
            existing = strongest_by_event.get(event_id)
            if existing is None or risk > float(existing["risk"]):
                strongest_by_event[event_id] = candidate

        ordered_events = sorted(
            strongest_by_event.items(),
            key=lambda item: (str(item[1]["timestamp"]), item[0]),
        )

        active: dict[str, float] = {}
        points: list[dict] = []
        for event_id, item in ordered_events:
            active[event_id] = float(item["risk"])
            aggregate = aggregate_company_risk(
                company_id=company_id,
                contributions=[
                    RiskContribution(event_id=key, propagated_risk=value)
                    for key, value in sorted(active.items())
                ],
            )
            points.append(
                {
                    "timestamp": item["timestamp"],
                    "risk_score": aggregate.aggregate_risk,
                    "risk_level": self._risk_level(aggregate.aggregate_risk),
                    "event_id": event_id,
                }
            )

        return {
            "company_id": company_id,
            "max_hops": max_hops,
            "points": points,
            "count": len(points),
        }
