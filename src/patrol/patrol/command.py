"""Чистая логика выбора команды: без rclpy, поэтому тестируется обычным pytest."""

import math
from typing import NamedTuple, Optional, Protocol


LINEAR_SPEED = 0.5
"""Скорость вперёд после получения позы, м/с (единицы turtlesim)."""

TURN_RATE = 0.3
"""Скорость поворота после получения позы, рад/с."""

PUBLISH_HZ = 10.0
"""Частота публикации команды по умолчанию, Гц."""

MAX_LINEAR = 1.0
MAX_ANGULAR = 1.0
MIN_HZ = 1.0
MAX_HZ = 30.0

LIMITS = {
    'linear_speed': (0.0, MAX_LINEAR),
    'turn_rate': (-MAX_ANGULAR, MAX_ANGULAR),
    'publish_hz': (MIN_HZ, MAX_HZ),
}
"""Допустимые диапазоны параметров patrol (границы включительно)."""


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


def validate_parameter(name: str, value: object) -> Optional[str]:
    """
    Проверить новое значение параметра patrol до его применения.

    Возвращает None, если значение допустимо, иначе текст причины отказа.
    Допустимы только конечные числа (не bool) внутри LIMITS[name].
    """
    if name not in LIMITS:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return f'{name}: ожидается число, получено {type(value).__name__}'
    number = float(value)
    if not math.isfinite(number):
        return f'{name}: ожидается конечное число, получено {number}'
    low, high = LIMITS[name]
    if not low <= number <= high:
        return f'{name}={number} вне диапазона [{low}, {high}]'
    return None


def validate_publish_hz(value: object) -> Optional[str]:
    """Проверить частоту публикации: конечное число в [1, 30] Гц."""
    return validate_parameter('publish_hz', value)


def period_for(publish_hz: float) -> float:
    """Период таймера для допустимой частоты: 1 / publish_hz."""
    return 1.0 / publish_hz
