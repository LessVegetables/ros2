"""Чистая логика адаптеров ПР07 (без rclpy): Ackermann → Twist и нормализация frames."""

from __future__ import annotations

import math
from typing import NamedTuple, Optional

WHEELBASE_M = 0.8
MAX_SPEED = 1.2
MAX_STEERING = 0.45
MAX_AGE_S = 0.25
GZ_PREFIX = 'course_ackermann/'


class TwistCommand(NamedTuple):
    """Скорости для geometry_msgs/Twist: linear.x и angular.z."""

    linear_x: float
    angular_z: float


ZERO = TwistCommand(0.0, 0.0)


def clamp(value: float, low: float, high: float) -> float:
    """Ограничить значение диапазоном [low, high]."""
    return max(low, min(high, value))


def drive_to_twist(speed: float, steering_angle: float, age_s: float,
                   max_age_s: float = MAX_AGE_S) -> tuple[TwistCommand, str]:
    """
    Перевести команду Ackermann в Twist для Gazebo AckermannSteering.

    v = clamp(speed, 0, 1.2); δ = clamp(angle, -0.45, 0.45); ω = v·tan(δ)/0.8.
    NaN/∞ в любом поле или возраст > max_age_s — нулевой Twist и причина.
    """
    if not all(math.isfinite(x) for x in (speed, steering_angle, age_s)):
        return ZERO, 'non_finite_command'
    if age_s > max_age_s:
        return ZERO, 'stale_command'
    if age_s < -max_age_s:
        return ZERO, 'command_from_future'
    v = clamp(speed, 0.0, MAX_SPEED)
    delta = clamp(steering_angle, -MAX_STEERING, MAX_STEERING)
    return TwistCommand(v, v * math.tan(delta) / WHEELBASE_M), ''


def strip_gz_prefix(frame_id: str) -> Optional[str]:
    """course_ackermann/odom → odom; другой префикс или пусто — None (отклонить)."""
    if not frame_id.startswith(GZ_PREFIX):
        return None
    rest = frame_id[len(GZ_PREFIX):]
    return rest if rest and '/' not in rest else None


def all_finite(values: list[float]) -> bool:
    """Все числа конечны (проверка pose/twist/covariance одометрии)."""
    return all(math.isfinite(v) for v in values)
