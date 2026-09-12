from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DirectAffectedCompany:
    """Company directly linked to an event through AFFECTS."""

    event_id: str
    company_id: str
    company_name: str
    severity: str


@dataclass(frozen=True, slots=True)
class SupplyEdge:
    """One canonical downstream SUPPLIES edge used for propagation."""

    source_company_id: str
    source_company_name: str
    target_company_id: str
    target_company_name: str
    dependency_weight: float
    weight_source: str


@dataclass(frozen=True, slots=True)
class TwoHopSupplyPath:
    """Exactly two downstream SUPPLIES edges from one source company."""

    source_company_id: str
    source_company_name: str
    hop_1_company_id: str
    hop_1_company_name: str
    hop_2_company_id: str
    hop_2_company_name: str
    hop_1_weight: float
    hop_1_weight_source: str
    hop_2_weight: float
    hop_2_weight_source: str


@dataclass(frozen=True, slots=True)
class OneHopExposure:
    """Explainable one-hop risk result for one downstream company."""

    event_id: str
    event_severity: str
    source_company_id: str
    source_company_name: str
    target_company_id: str
    target_company_name: str
    relationship_type: str
    dependency_weight: float
    weight_source: str
    hop_distance: int
    initial_risk: float
    distance_decay: float
    propagated_risk: float


@dataclass(frozen=True, slots=True)
class TwoHopExposure:
    """Explainable two-hop risk result for one indirect downstream company."""

    event_id: str
    event_severity: str
    source_company_id: str
    source_company_name: str
    hop_1_company_id: str
    hop_1_company_name: str
    hop_2_company_id: str
    hop_2_company_name: str
    hop_1_weight: float
    hop_1_weight_source: str
    hop_2_weight: float
    hop_2_weight_source: str
    hop_distance: int
    initial_risk: float
    path_dependency: float
    distance_decay: float
    propagated_risk: float
