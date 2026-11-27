"""ПР05: выбор профиля QoS для sensor_pose."""

from patrol.qos import reliability_from_name, sensor_profile
import pytest
from rclpy.qos import HistoryPolicy, ReliabilityPolicy


def test_names_map_to_policies() -> None:
    assert reliability_from_name('reliable') == ReliabilityPolicy.RELIABLE
    assert reliability_from_name('best_effort') == ReliabilityPolicy.BEST_EFFORT


def test_unknown_name_rejected() -> None:
    with pytest.raises(ValueError):
        reliability_from_name('sometimes')


def test_sensor_profile_is_keep_last_best_effort_by_default() -> None:
    profile = sensor_profile()
    assert profile.reliability == ReliabilityPolicy.BEST_EFFORT
    assert profile.history == HistoryPolicy.KEEP_LAST
    assert profile.depth == 10
