"""Профили QoS для потока позы (ПР05): чистые функции без запуска ноды."""

from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

RELIABILITY = {
    'reliable': ReliabilityPolicy.RELIABLE,
    'best_effort': ReliabilityPolicy.BEST_EFFORT,
}


def reliability_from_name(name: str) -> ReliabilityPolicy:
    """Перевести имя из аргумента launch в политику; неизвестное имя — ошибка."""
    try:
        return RELIABILITY[name]
    except KeyError:
        raise ValueError(
            f'reliability должна быть одной из {sorted(RELIABILITY)}, получено {name!r}'
        ) from None


def sensor_profile(reliability: str = 'best_effort', depth: int = 10) -> QoSProfile:
    """Профиль сенсорного потока: keep_last(depth), volatile, заданная надёжность."""
    return QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=depth,
                      reliability=reliability_from_name(reliability))
