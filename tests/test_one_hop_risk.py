from __future__ import annotations

import pytest

from src.risk.models import DirectAffectedCompany, SupplyEdge
from src.risk.scoring import severity_to_initial_risk
from src.risk.service import RiskPropagationService


class FakeRiskRepository:
    def get_directly_affected_companies(
        self,
        event_id: str,
    ) -> list[DirectAffectedCompany]:
        return [
            DirectAffectedCompany(
                event_id=event_id,
                company_id="tsmc",
                company_name="TSMC",
                severity="critical",
            )
        ]

    def get_one_hop_downstream(
        self,
        company_id: str,
    ) -> list[SupplyEdge]:
        assert company_id == "tsmc"
        return [
            SupplyEdge(
                source_company_id="tsmc",
                source_company_name="TSMC",
                target_company_id="nvidia",
                target_company_name="NVIDIA",
                dependency_weight=0.80,
                weight_source="relationship",
            )
        ]


def test_severity_to_initial_risk() -> None:
    assert severity_to_initial_risk("unknown") == pytest.approx(0.0)
    assert severity_to_initial_risk("low") == pytest.approx(0.25)
    assert severity_to_initial_risk("medium") == pytest.approx(0.50)
    assert severity_to_initial_risk("high") == pytest.approx(0.75)
    assert severity_to_initial_risk("critical") == pytest.approx(1.0)


def test_one_hop_propagation_uses_supply_edge_as_hop_one() -> None:
    service = RiskPropagationService(FakeRiskRepository())  # type: ignore[arg-type]

    exposures = service.calculate_one_hop_exposure("event-001")

    assert len(exposures) == 1

    exposure = exposures[0]

    assert exposure.source_company_id == "tsmc"
    assert exposure.target_company_id == "nvidia"
    assert exposure.hop_distance == 1
    assert exposure.initial_risk == pytest.approx(1.0)
    assert exposure.dependency_weight == pytest.approx(0.80)
    assert exposure.distance_decay == pytest.approx(1.0)
    assert exposure.propagated_risk == pytest.approx(0.80)


def test_empty_event_id_is_rejected() -> None:
    service = RiskPropagationService(FakeRiskRepository())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_id"):
        service.calculate_one_hop_exposure("   ")
