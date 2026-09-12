from __future__ import annotations

import pytest

from src.risk.models import DirectAffectedCompany, TwoHopSupplyPath
from src.risk.service import RiskPropagationService


class FakeRiskRepository:
    def get_directly_affected_companies(
        self,
        event_id: str,
    ) -> list[DirectAffectedCompany]:
        return [
            DirectAffectedCompany(
                event_id=event_id,
                company_id="company-a",
                company_name="Company A",
                severity="critical",
            )
        ]

    def get_two_hop_downstream(
        self,
        company_id: str,
    ) -> list[TwoHopSupplyPath]:
        assert company_id == "company-a"
        return [
            TwoHopSupplyPath(
                source_company_id="company-a",
                source_company_name="Company A",
                hop_1_company_id="company-b",
                hop_1_company_name="Company B",
                hop_2_company_id="company-c",
                hop_2_company_name="Company C",
                hop_1_weight=0.80,
                hop_1_weight_source="relationship",
                hop_2_weight=0.60,
                hop_2_weight_source="relationship",
            )
        ]


def test_two_hop_propagation_uses_two_supply_edges() -> None:
    service = RiskPropagationService(FakeRiskRepository())  # type: ignore[arg-type]

    exposures = service.calculate_two_hop_exposure("event-001")

    assert len(exposures) == 1

    exposure = exposures[0]

    assert exposure.source_company_id == "company-a"
    assert exposure.hop_1_company_id == "company-b"
    assert exposure.hop_2_company_id == "company-c"
    assert exposure.hop_distance == 2
    assert exposure.initial_risk == pytest.approx(1.0)
    assert exposure.hop_1_weight == pytest.approx(0.80)
    assert exposure.hop_2_weight == pytest.approx(0.60)
    assert exposure.path_dependency == pytest.approx(0.48)
    assert exposure.distance_decay == pytest.approx(0.70)
    assert exposure.propagated_risk == pytest.approx(0.336)


def test_two_hop_expected_day40_example() -> None:
    repository = FakeRiskRepository()
    affected = repository.get_directly_affected_companies("event-002")[0]

    affected = DirectAffectedCompany(
        event_id=affected.event_id,
        company_id=affected.company_id,
        company_name=affected.company_name,
        severity="high",
    )

    class HighSeverityRepository(FakeRiskRepository):
        def get_directly_affected_companies(
            self,
            event_id: str,
        ) -> list[DirectAffectedCompany]:
            return [
                DirectAffectedCompany(
                    event_id=event_id,
                    company_id=affected.company_id,
                    company_name=affected.company_name,
                    severity=affected.severity,
                )
            ]

    service = RiskPropagationService(HighSeverityRepository())  # type: ignore[arg-type]
    exposure = service.calculate_two_hop_exposure("event-002")[0]

    assert exposure.initial_risk == pytest.approx(0.75)
    assert exposure.path_dependency == pytest.approx(0.48)
    assert exposure.distance_decay == pytest.approx(0.70)
    assert exposure.propagated_risk == pytest.approx(0.252)


def test_two_hop_empty_event_id_is_rejected() -> None:
    service = RiskPropagationService(FakeRiskRepository())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_id"):
        service.calculate_two_hop_exposure("   ")
