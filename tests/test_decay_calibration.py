import pytest

from scripts.evaluate_decay_factors import (
    CANDIDATE_DECAY_FACTORS,
    build_decay_profile,
    evaluate_candidates,
)
from src.risk.mathematics import DEFAULT_DECAY_FACTOR


def test_candidate_set_contains_selected_default() -> None:
    assert DEFAULT_DECAY_FACTOR in CANDIDATE_DECAY_FACTORS


def test_default_decay_profile_matches_day42_baseline() -> None:
    profile = build_decay_profile(DEFAULT_DECAY_FACTOR)

    assert profile.hop_1 == pytest.approx(1.0)
    assert profile.hop_2 == pytest.approx(0.70)
    assert profile.hop_3 == pytest.approx(0.49)


def test_risk_retention_decreases_with_distance() -> None:
    for profile in evaluate_candidates():
        assert profile.hop_1 >= profile.hop_2 >= profile.hop_3


def test_higher_lambda_retains_more_indirect_risk() -> None:
    profiles = evaluate_candidates()

    for lower, higher in zip(profiles, profiles[1:]):
        assert lower.hop_2 < higher.hop_2
        assert lower.hop_3 < higher.hop_3


def test_candidate_profiles_follow_exponential_formula() -> None:
    for profile in evaluate_candidates():
        assert profile.hop_1 == pytest.approx(1.0)
        assert profile.hop_2 == pytest.approx(profile.decay_factor)
        assert profile.hop_3 == pytest.approx(profile.decay_factor**2)
