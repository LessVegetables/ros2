"""Функциональные тесты чистой логики patrol (без запуска ROS)."""

from dataclasses import dataclass

from patrol.command import choose_command, clamp, Command, STOP


@dataclass
class FakePose:
    """Заменитель turtlesim_msgs/msg/Pose с теми же полями."""

    x: float = 5.54
    y: float = 5.54
    theta: float = 0.0


def test_no_pose_gives_zero_command() -> None:
    assert choose_command(None) == STOP
    assert choose_command(None) == Command(0.0, 0.0)


def test_regular_pose_gives_patrol_command() -> None:
    assert choose_command(FakePose()) == Command(0.5, 0.3)


def test_command_does_not_depend_on_position() -> None:
    assert choose_command(FakePose(1.0, 9.0, -3.0)) == choose_command(FakePose())


def test_command_is_clamped() -> None:
    assert choose_command(FakePose(), linear_speed=5.0, turn_rate=-7.0) == Command(1.0, -1.0)


def test_clamp() -> None:
    assert clamp(0.4, 1.0) == 0.4
    assert clamp(2.0, 1.0) == 1.0
    assert clamp(-2.0, 1.0) == -1.0
