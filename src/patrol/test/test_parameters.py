"""ПР04: проверка параметров patrol до применения (чистые функции, без ROS)."""

import math

from patrol.command import period_for, validate_parameter, validate_publish_hz
import pytest


def test_normal_rate_change_10_to_5() -> None:
    assert validate_publish_hz(10.0) is None
    assert validate_publish_hz(5.0) is None
    assert period_for(5.0) == pytest.approx(0.2)
    assert period_for(10.0) == pytest.approx(0.1)


@pytest.mark.parametrize('value', [0.0, 0, -1.0, -10.0, math.nan, math.inf, -math.inf,
                                   0.5, 30.5, 1000.0])
def test_invalid_rate_rejected(value: float) -> None:
    assert validate_publish_hz(value) is not None


def test_zero_reason_mentions_range() -> None:
    reason = validate_publish_hz(0.0)
    assert reason is not None and '[1.0, 30.0]' in reason


def test_nan_reason_mentions_finite() -> None:
    reason = validate_publish_hz(math.nan)
    assert reason is not None and 'конечное' in reason


@pytest.mark.parametrize('value', [1.0, 1, 15.5, 30.0])
def test_rate_bounds_inclusive(value: float) -> None:
    assert validate_publish_hz(value) is None


def test_non_number_rejected() -> None:
    assert validate_publish_hz('10') is not None
    assert validate_publish_hz(True) is not None


@pytest.mark.parametrize('name,value,ok', [
    ('linear_speed', 0.0, True),
    ('linear_speed', 1.0, True),
    ('linear_speed', 0.8, True),
    ('linear_speed', 2.0, False),
    ('linear_speed', -0.1, False),
    ('linear_speed', math.nan, False),
    ('turn_rate', -1.0, True),
    ('turn_rate', 0.6, True),
    ('turn_rate', 1.5, False),
    ('turn_rate', math.inf, False),
])
def test_speed_and_turn_limits(name: str, value: float, ok: bool) -> None:
    assert (validate_parameter(name, value) is None) is ok


def test_unknown_parameter_not_checked() -> None:
    assert validate_parameter('use_sim_time', True) is None
