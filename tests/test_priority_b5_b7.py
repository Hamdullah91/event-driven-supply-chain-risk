from src.api.services.risk import RiskAnalyticsService
from src.events.facility_resolution import resolve_facility_mentions


def test_facility_resolution_matches_explicit_seeded_name():
    matches = resolve_facility_mentions(
        ["Fire reported at TSMC Fab 18 in Tainan"]
    )
    assert ("tsmc_fab_18", "facility_name_exact") in matches


def test_facility_resolution_normalizes_case_and_hyphenation():
    matches = resolve_facility_mentions(
        ["Incident reported at tsmc-fab 18"]
    )
    assert ("tsmc_fab_18", "facility_name_exact") in matches


def test_facility_resolution_does_not_guess_from_city_only():
    assert resolve_facility_mentions(["A disruption occurred in Singapore"]) == []


def test_facility_resolution_does_not_fuzzy_match_ambiguous_partial_name():
    assert resolve_facility_mentions(["An Intel manufacturing site had delays"]) == []


class HistoryRepository:
    def get_company_risk_history(self, company_id, *, max_hops, limit):
        assert company_id == "nvidia"
        # Intentionally out of order, with two paths for e1. The service must
        # reconstruct chronologically and emit only the strongest e1 path.
        return [
            {
                "event_id": "e2",
                "severity": "medium",
                "timestamp": "2026-01-02T00:00:00Z",
                "hop_distance": 2,
                "dependency_weights": [1.0, 1.0],
            },
            {
                "event_id": "e1",
                "severity": "high",
                "timestamp": "2026-01-01T00:00:00Z",
                "hop_distance": 2,
                "dependency_weights": [0.5, 1.0],
            },
            {
                "event_id": "e1",
                "severity": "high",
                "timestamp": "2026-01-01T00:00:00Z",
                "hop_distance": 1,
                "dependency_weights": [1.0],
            },
        ][:limit]


def test_risk_history_reconstructs_chronological_cumulative_series():
    result = RiskAnalyticsService(HistoryRepository()).get_risk_history(
        "nvidia",
        max_hops=3,
        limit=100,
    )
    assert result["count"] == 2
    assert result["points"][0]["event_id"] == "e1"
    assert result["points"][0]["timestamp"] < result["points"][1]["timestamp"]
    assert result["points"][0]["risk_score"] == 0.75
    assert result["points"][0]["risk_level"] == "CRITICAL"
    assert result["points"][1]["risk_score"] > result["points"][0]["risk_score"]
    assert result["points"][1]["event_id"] == "e2"
