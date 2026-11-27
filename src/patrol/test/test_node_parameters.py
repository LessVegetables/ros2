"""ПР04: живая нода patrol отклоняет недопустимую частоту и сохраняет таймер."""

from collections.abc import Iterator
import math

from patrol.patrol import Patrol
import pytest
import rclpy
from rclpy.parameter import Parameter


@pytest.fixture
def node() -> Iterator[Patrol]:
    rclpy.init()
    patrol = Patrol()
    yield patrol
    patrol.destroy_node()
    rclpy.try_shutdown()


def timer_period_s(node: Patrol) -> float:
    return node._timer.timer_period_ns * 1e-9


def test_defaults(node: Patrol) -> None:
    assert node.get_parameter('linear_speed').value == 0.5
    assert node.get_parameter('turn_rate').value == 0.3
    assert node.get_parameter('publish_hz').value == 10.0
    assert timer_period_s(node) == pytest.approx(0.1)


def test_valid_rate_recreates_single_timer(node: Patrol) -> None:
    old_timer = node._timer
    result = node.set_parameters([Parameter('publish_hz', value=5.0)])[0]
    assert result.successful
    assert node._timer is not old_timer
    assert timer_period_s(node) == pytest.approx(0.2)
    assert len(list(node.timers)) == 1


@pytest.mark.parametrize('bad', [0.0, -1.0, math.nan, 31.0])
def test_invalid_rate_rejected_state_kept(node: Patrol, bad: float) -> None:
    old_timer = node._timer
    result = node.set_parameters([Parameter('publish_hz', value=bad)])[0]
    assert not result.successful
    assert result.reason
    assert node.get_parameter('publish_hz').value == 10.0
    assert node._timer is old_timer
    assert timer_period_s(node) == pytest.approx(0.1)


def test_speed_out_of_range_rejected(node: Patrol) -> None:
    assert node.set_parameters([Parameter('linear_speed', value=0.8)])[0].successful
    assert not node.set_parameters([Parameter('linear_speed', value=2.0)])[0].successful
    assert node.get_parameter('linear_speed').value == 0.8
