import pytest

from src.risk.mathematics import (
    DEFAULT_DECAY_FACTOR,
    calculate_distance_decay,
    calculate_path_dependency,
    calculate_path_risk,
)


def test_default_decay_factor_is_point_seven() -> None:
    assert DEFAULT_DECAY_FACTOR == pytest.approx(0.70)


def test_hop_one_has_no_additional_distance_decay() -> None:
    assert calculate_distance_decay(1) == pytest.approx(1.0)


def test_hop_two_applies_single_decay() -> None:
    assert calculate_distance_decay(2) == pytest.approx(0.70)


def test_hop_three_applies_squared_decay() -> None:
    assert calculate_distance_decay(3) == pytest.approx(0.49)


def test_path_dependency_multiplies_all_relationship_weights() -> None:
    result = calculate_path_dependency(
        [0.90, 0.80, 0.60]
    )

    assert result == pytest.approx(0.432)


def test_one_hop_risk() -> None:
    result = calculate_path_risk(
        initial_risk=0.90,
        dependency_weights=[0.90],
    )

    assert result.hop_distance == 1
    assert result.path_dependency == pytest.approx(0.90)
    assert result.distance_decay == pytest.approx(1.0)
    assert result.propagated_risk == pytest.approx(0.81)


def test_two_hop_risk() -> None:
    result = calculate_path_risk(
        initial_risk=0.90,
        dependency_weights=[0.90, 0.80],
    )

    assert result.hop_distance == 2
    assert result.path_dependency == pytest.approx(0.72)
    assert result.distance_decay == pytest.approx(0.70)
    assert result.propagated_risk == pytest.approx(0.4536)


def test_three_hop_risk() -> None:
    result = calculate_path_risk(
        initial_risk=0.90,
        dependency_weights=[0.90, 0.80, 0.60],
    )

    assert result.hop_distance == 3
    assert result.path_dependency == pytest.approx(0.432)
    assert result.distance_decay == pytest.approx(0.49)
    assert result.propagated_risk == pytest.approx(
        0.190512
    )


@pytest.mark.parametrize(
    "invalid_initial_risk",
    [-0.01, 1.01],
)
def test_invalid_initial_risk_rejected(
    invalid_initial_risk: float,
) -> None:
    with pytest.raises(ValueError):
        calculate_path_risk(
            initial_risk=invalid_initial_risk,
            dependency_weights=[0.8],
        )


@pytest.mark.parametrize(
    "invalid_weight",
    [-0.01, 1.01],
)
def test_invalid_dependency_weight_rejected(
    invalid_weight: float,
) -> None:
    with pytest.raises(ValueError):
        calculate_path_risk(
            initial_risk=0.8,
            dependency_weights=[invalid_weight],
        )


def test_empty_dependency_path_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_path_risk(
            initial_risk=0.8,
            dependency_weights=[],
        )


def test_more_than_three_hops_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_path_risk(
            initial_risk=0.8,
            dependency_weights=[
                0.9,
                0.8,
                0.7,
                0.6,
            ],
        )


@pytest.mark.parametrize(
    "invalid_decay",
    [0.0, -0.1, 1.01],
)
def test_invalid_decay_factor_rejected(
    invalid_decay: float,
) -> None:
    with pytest.raises(ValueError):
        calculate_path_risk(
            initial_risk=0.8,
            dependency_weights=[0.9],
            decay_factor=invalid_decay,
        )