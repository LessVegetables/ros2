"""Чистая логика выбора команды: без rclpy, поэтому тестируется обычным pytest."""

from typing import NamedTuple, Optional, Protocol


LINEAR_SPEED = 0.5
"""Скорость вперёд после получения позы, м/с (единицы turtlesim)."""

TURN_RATE = 0.3
"""Скорость поворота после получения позы, рад/с."""

MAX_LINEAR = 1.0
MAX_ANGULAR = 1.0


class PoseLike(Protocol):
    """Минимум полей позы turtlesim, нужных логике (x, y, theta)."""

    x: float
    y: float
    theta: float


class Command(NamedTuple):
    """Пара скоростей, из которой нода собирает geometry_msgs/msg/Twist."""

    linear_x: float
    angular_z: float


STOP = Command(0.0, 0.0)


def clamp(value: float, limit: float) -> float:
    """Ограничить value диапазоном [-limit, limit]."""
    return max(-limit, min(limit, value))


def choose_command(pose: Optional[PoseLike],
                   linear_speed: float = LINEAR_SPEED,
                   turn_rate: float = TURN_RATE) -> Command:
    """
    Выбрать команду по последней позе.

    До первой позы робот стоит (нулевая команда). После — едет вперёд и
    поворачивает с заданными скоростями, ограниченными MAX_LINEAR/MAX_ANGULAR.
    """
    if pose is None:
        return STOP
    return Command(clamp(linear_speed, MAX_LINEAR), clamp(turn_rate, MAX_ANGULAR))
