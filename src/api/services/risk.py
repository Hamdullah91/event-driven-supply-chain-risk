from __future__ import annotations

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

        strongest_by_company: dict[str, dict] = {}

        for row in rows:
            weights = [
                float(item["dependency_weight"])
                for item in (row["path_relationships"] or [])
            ]
            result = calculate_path_risk(
                initial_risk=1.0,
                dependency_weights=weights,
            )

            target_id = str(row["target_company_id"])
            candidate = {
                "company_id": target_id,
                "company_name": str(row["target_company_name"]),
                "hop_distance": int(row["hop_distance"]),
                "transmission_factor": result.propagated_risk,
                "path": list(row["path_nodes"] or []),
            }

            existing = strongest_by_company.get(target_id)
            if (
                existing is None
                or candidate["transmission_factor"]
                > existing["transmission_factor"]
            ):
                strongest_by_company[target_id] = candidate

        companies = sorted(
            strongest_by_company.values(),
            key=lambda item: (
                item["hop_distance"],
                -item["transmission_factor"],
                item["company_id"],
            ),
        )
        hop_counts = {
            str(hop): sum(
                1
                for company in companies
                if company["hop_distance"] == hop
            )
            for hop in range(1, max_hops + 1)
        }

        return {
            "company_id": company_id,
            "max_hops": max_hops,
            "affected_company_count": len(companies),
            "hop_counts": hop_counts,
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
            initial_risk = severity_to_initial_risk(severity)
            hop_distance = int(row["hop_distance"])
            weights = [
                float(weight)
                for weight in (row["dependency_weights"] or [])
            ]

            if hop_distance == 0:
                path_dependency = 1.0
                distance_decay = 1.0
                propagated_risk = initial_risk
            else:
                result = calculate_path_risk(
                    initial_risk=initial_risk,
                    dependency_weights=weights,
                )
                path_dependency = result.path_dependency
                distance_decay = result.distance_decay
                propagated_risk = result.propagated_risk

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
                    "hop_distance": hop_distance,
                    "initial_risk": initial_risk,
                    "path_dependency": path_dependency,
                    "distance_decay": distance_decay,
                    "propagated_risk": propagated_risk,
                    "path": list(row.get("path_nodes") or []),
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

    def get_company_risk(
        self,
        company_id: str,
        *,
        max_hops: int = 3,
    ) -> dict:
        exposure = self.get_exposure(company_id, max_hops=max_hops)

        strongest_per_event: dict[str, float] = {}
        for item in exposure["exposures"]:
            event_id = str(item["event_id"])
            propagated_risk = float(item["propagated_risk"])
            strongest_per_event[event_id] = max(
                propagated_risk,
                strongest_per_event.get(event_id, 0.0),
            )

        aggregation = aggregate_company_risk(
            company_id=company_id,
            contributions=[
                RiskContribution(
                    event_id=event_id,
                    propagated_risk=propagated_risk,
                )
                for event_id, propagated_risk in sorted(
                    strongest_per_event.items()
                )
            ],
        )

        score = aggregation.aggregate_risk
        if score >= 0.75:
            level = "CRITICAL"
        elif score >= 0.50:
            level = "HIGH"
        elif score >= 0.25:
            level = "MEDIUM"
        elif score > 0.0:
            level = "LOW"
        else:
            level = "NONE"

        return {
            "company_id": company_id,
            "risk_score": score,
            "risk_level": level,
            "contributing_event_count": aggregation.event_count,
            "max_hops": max_hops,
        }
