from __future__ import annotations

import pytest

from src.risk.models import DirectAffectedCompany, ThreeHopSupplyPath
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
                severity="high",
            )
        ]

    def get_three_hop_downstream(
        self,
        company_id: str,
    ) -> list[ThreeHopSupplyPath]:
        assert company_id == "company-a"
        return [
            ThreeHopSupplyPath(
                source_company_id="company-a",
                source_company_name="Company A",
                hop_1_company_id="company-b",
                hop_1_company_name="Company B",
                hop_2_company_id="company-c",
                hop_2_company_name="Company C",
                hop_3_company_id="company-d",
                hop_3_company_name="Company D",
                hop_1_weight=0.80,
                hop_1_weight_source="relationship",
                hop_2_weight=0.75,
                hop_2_weight_source="relationship",
                hop_3_weight=0.50,
                hop_3_weight_source="relationship",
            )
        ]


def test_three_hop_propagation_uses_three_supply_edges() -> None:
    service = RiskPropagationService(FakeRiskRepository())  # type: ignore[arg-type]

    exposures = service.calculate_three_hop_exposure("event-001")

    assert len(exposures) == 1

    exposure = exposures[0]

    assert exposure.source_company_id == "company-a"
    assert exposure.hop_1_company_id == "company-b"
    assert exposure.hop_2_company_id == "company-c"
    assert exposure.hop_3_company_id == "company-d"
    assert exposure.hop_distance == 3
    assert exposure.initial_risk == pytest.approx(0.75)
    assert exposure.hop_1_weight == pytest.approx(0.80)
    assert exposure.hop_2_weight == pytest.approx(0.75)
    assert exposure.hop_3_weight == pytest.approx(0.50)
    assert exposure.path_dependency == pytest.approx(0.30)
    assert exposure.distance_decay == pytest.approx(0.49)
    assert exposure.propagated_risk == pytest.approx(0.11025)


def test_three_hop_default_weight_path_is_supported() -> None:
    class DefaultWeightRepository(FakeRiskRepository):
        def get_three_hop_downstream(
            self,
            company_id: str,
        ) -> list[ThreeHopSupplyPath]:
            assert company_id == "company-a"
            return [
                ThreeHopSupplyPath(
                    source_company_id="company-a",
                    source_company_name="Company A",
                    hop_1_company_id="company-b",
                    hop_1_company_name="Company B",
                    hop_2_company_id="company-c",
                    hop_2_company_name="Company C",
                    hop_3_company_id="company-d",
                    hop_3_company_name="Company D",
                    hop_1_weight=1.0,
                    hop_1_weight_source="default",
                    hop_2_weight=1.0,
                    hop_2_weight_source="default",
                    hop_3_weight=1.0,
                    hop_3_weight_source="default",
                )
            ]

    service = RiskPropagationService(DefaultWeightRepository())  # type: ignore[arg-type]
    exposure = service.calculate_three_hop_exposure("event-002")[0]

    assert exposure.path_dependency == pytest.approx(1.0)
    assert exposure.distance_decay == pytest.approx(0.49)
    assert exposure.propagated_risk == pytest.approx(0.3675)


def test_three_hop_empty_event_id_is_rejected() -> None:
    service = RiskPropagationService(FakeRiskRepository())  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_id"):
        service.calculate_three_hop_exposure("   ")
