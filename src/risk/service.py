from __future__ import annotations

from src.risk.mathematics import calculate_path_risk
from src.risk.models import OneHopExposure
from src.risk.repository import RiskRepository
from src.risk.scoring import severity_to_initial_risk


class RiskPropagationService:
    """Coordinate graph traversal and deterministic risk mathematics."""

    def __init__(self, repository: RiskRepository) -> None:
        self.repository = repository

    def calculate_one_hop_exposure(
        self,
        event_id: str,
    ) -> list[OneHopExposure]:
        if not event_id.strip():
            raise ValueError("event_id must not be empty.")

        affected_companies = self.repository.get_directly_affected_companies(
            event_id
        )

        exposures: list[OneHopExposure] = []

        for affected in affected_companies:
            initial_risk = severity_to_initial_risk(affected.severity)
            downstream_edges = self.repository.get_one_hop_downstream(
                affected.company_id
            )

            for edge in downstream_edges:
                result = calculate_path_risk(
                    initial_risk=initial_risk,
                    dependency_weights=[edge.dependency_weight],
                )

                exposures.append(
                    OneHopExposure(
                        event_id=affected.event_id,
                        event_severity=affected.severity,
                        source_company_id=edge.source_company_id,
                        source_company_name=edge.source_company_name,
                        target_company_id=edge.target_company_id,
                        target_company_name=edge.target_company_name,
                        relationship_type="SUPPLIES",
                        dependency_weight=edge.dependency_weight,
                        weight_source=edge.weight_source,
                        hop_distance=result.hop_distance,
                        initial_risk=result.initial_risk,
                        distance_decay=result.distance_decay,
                        propagated_risk=result.propagated_risk,
                    )
                )

        return exposures
