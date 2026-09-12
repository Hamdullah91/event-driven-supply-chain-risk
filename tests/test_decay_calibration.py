import pytest

from scripts.evaluate_decay_factors import (
    CANDIDATE_DECAY_FACTORS,
    build_decay_profile,
    evaluate_candidates,
)
from src.risk.config import RiskPropagationConfig
from src.risk.mathematics import DEFAULT_DECAY_FACTOR, calculate_path_risk


def test_candidate_set_contains_selected_default() -> None:
    assert DEFAULT_DECAY_FACTOR in CANDIDATE_DECAY_FACTORS


def test_candidate_set_includes_midpoint_point_seven_five() -> None:
    assert 0.75 in CANDIDATE_DECAY_FACTORS


def test_default_decay_profile_matches_day42_baseline() -> None:
    profile = build_decay_profile(DEFAULT_DECAY_FACTOR)

    assert profile.hop_1 == pytest.approx(1.0)
    assert profile.hop_2 == pytest.approx(0.70)
    assert profile.hop_3 == pytest.approx(0.49)


def test_risk_retention_decreases_with_distance() -> None:
    for profile in evaluate_candidates():
        assert profile.hop_1 >= profile.hop_2 >= profile.hop_3


def test_path_risk_decreases_across_controlled_three_hop_scenario() -> None:
    for profile in evaluate_candidates():
        assert profile.hop_1_risk > profile.hop_2_risk > profile.hop_3_risk


def test_higher_lambda_retains_more_indirect_risk() -> None:
    profiles = evaluate_candidates()

    for lower, higher in zip(profiles, profiles[1:]):
        assert lower.hop_2 < higher.hop_2
        assert lower.hop_3 < higher.hop_3
        assert lower.hop_2_risk < higher.hop_2_risk
        assert lower.hop_3_risk < higher.hop_3_risk


def test_candidate_profiles_follow_exponential_formula() -> None:
    for profile in evaluate_candidates():
        assert profile.hop_1 == pytest.approx(1.0)
        assert profile.hop_2 == pytest.approx(profile.decay_factor)
        assert profile.hop_3 == pytest.approx(profile.decay_factor**2)


def test_zero_relationship_weight_blocks_path_risk() -> None:
    result = calculate_path_risk(
        initial_risk=1.0,
        dependency_weights=[0.9, 0.0],
        decay_factor=0.75,
    )

    assert result.path_dependency == pytest.approx(0.0)
    assert result.propagated_risk == pytest.approx(0.0)


def test_risk_propagation_config_defaults_to_project_baseline() -> None:
    config = RiskPropagationConfig()

    assert config.max_hops == 3
    assert config.decay_factor == pytest.approx(DEFAULT_DECAY_FACTOR)


@pytest.mark.parametrize("invalid_decay", [0.0, -0.1, 1.01])
def test_risk_propagation_config_rejects_invalid_decay(
    invalid_decay: float,
) -> None:
    with pytest.raises(ValueError):
        RiskPropagationConfig(decay_factor=invalid_decay)


@pytest.mark.parametrize("invalid_hops", [0, 4])
def test_risk_propagation_config_rejects_unsupported_hop_limit(
    invalid_hops: int,
) -> None:
    with pytest.raises(ValueError):
        RiskPropagationConfig(max_hops=invalid_hops)
