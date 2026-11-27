"""ПР07: адаптер Ackermann → Twist и нормализация одометрии (чистые функции)."""

import math

from course_simulation.drive_logic import drive_to_twist, strip_gz_prefix, ZERO
import pytest


def test_straight() -> None:
    cmd, reason = drive_to_twist(0.8, 0.0, 0.0)
    assert reason == '' and cmd.linear_x == pytest.approx(0.8) and cmd.angular_z == 0.0


def test_turn_uses_wheelbase() -> None:
    cmd, reason = drive_to_twist(1.0, 0.3, 0.05)
    assert reason == ''
    assert cmd.angular_z == pytest.approx(1.0 * math.tan(0.3) / 0.8)


def test_limits() -> None:
    cmd, _ = drive_to_twist(5.0, -1.0, 0.0)
    assert cmd.linear_x == pytest.approx(1.2)
    assert cmd.angular_z == pytest.approx(1.2 * math.tan(-0.45) / 0.8)


def test_zero_speed_no_spin_in_place() -> None:
    cmd, reason = drive_to_twist(0.0, 0.45, 0.0)
    assert reason == '' and cmd == ZERO


def test_reverse_clamped_to_zero() -> None:
    cmd, _ = drive_to_twist(-1.0, 0.2, 0.0)
    assert cmd == ZERO


def test_stale_command_gives_zero() -> None:
    assert drive_to_twist(1.0, 0.2, 0.26) == (ZERO, 'stale_command')
    assert drive_to_twist(1.0, 0.2, 0.25)[1] == ''


@pytest.mark.parametrize('speed,angle', [(math.nan, 0.0), (1.0, math.inf), (-math.inf, 0.1)])
def test_non_finite_gives_zero(speed: float, angle: float) -> None:
    assert drive_to_twist(speed, angle, 0.0) == (ZERO, 'non_finite_command')


def test_strip_prefix() -> None:
    assert strip_gz_prefix('course_ackermann/odom') == 'odom'
    assert strip_gz_prefix('course_ackermann/base_link') == 'base_link'
    assert strip_gz_prefix('other_robot/odom') is None
    assert strip_gz_prefix('odom') is None
    assert strip_gz_prefix('course_ackermann/') is None
