"""Преобразование SceneDescription v1: JSON ↔ robotics_course_interfaces/msg/SceneDescription."""

from __future__ import annotations

from typing import Any

from robotics_course_interfaces.msg import SceneDescription

STATUS = {'valid': SceneDescription.STATUS_VALID, 'unknown': SceneDescription.STATUS_UNKNOWN}
LIGHT = {
    'none': SceneDescription.LIGHT_NONE,
    'red': SceneDescription.LIGHT_RED,
    'yellow': SceneDescription.LIGHT_YELLOW,
    'green': SceneDescription.LIGHT_GREEN,
    'unknown': SceneDescription.LIGHT_UNKNOWN,
}
SIGN = {
    'none': SceneDescription.SIGN_NONE,
    'left': SceneDescription.SIGN_LEFT,
    'right': SceneDescription.SIGN_RIGHT,
    'straight': SceneDescription.SIGN_STRAIGHT,
    'unknown': SceneDescription.SIGN_UNKNOWN,
}
DISTANCES = (
    ('stop_line_distance_m', 'has_stop_line'),
    ('turn_distance_m', 'has_turn'),
    ('obstacle_distance_m', 'has_obstacle'),
)


class ConversionError(ValueError):
    """Неизвестное значение enum: результат должен стать unknown/invalid_schema."""


def stamp_parts(stamp_s: float) -> tuple[int, int]:
    """Целая часть — sec, дробная × 10⁹ с округлением — nanosec."""
    sec = int(stamp_s)
    nanosec = round((stamp_s - sec) * 1e9)
    if nanosec >= 1_000_000_000:
        sec, nanosec = sec + 1, nanosec - 1_000_000_000
    return sec, nanosec


def to_msg(scene: dict[str, Any]) -> SceneDescription:
    """JSON-словарь (уже проверенный схемой) → ROS-сообщение."""
    try:
        status = STATUS[scene['status']]
        light = LIGHT[scene['traffic_light']]
        sign = SIGN[scene['direction_sign']]
    except KeyError as error:
        raise ConversionError(f'неизвестное значение enum: {error}') from error
    msg = SceneDescription()
    msg.header.stamp.sec, msg.header.stamp.nanosec = stamp_parts(float(scene['stamp_s']))
    msg.header.frame_id = scene['frame_id']
    msg.version = int(scene['version'])
    msg.status = status
    msg.status_reason = scene['status_reason']
    msg.traffic_light = light
    msg.direction_sign = sign
    msg.lane_offset_m = float(scene['lane_offset_m'])
    for field, flag in DISTANCES:
        value = scene[field]
        setattr(msg, flag, value is not None)
        setattr(msg, field, 0.0 if value is None else float(value))
    msg.confidence = float(scene['confidence'])
    msg.source = scene['source']
    return msg


def from_msg(msg: SceneDescription) -> dict[str, Any]:
    """ROS-сообщение → JSON-словарь; has_* = false превращается в null."""
    inv_status = {v: k for k, v in STATUS.items()}
    inv_light = {v: k for k, v in LIGHT.items()}
    inv_sign = {v: k for k, v in SIGN.items()}
    try:
        scene: dict[str, Any] = {
            'version': int(msg.version),
            'stamp_s': msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
            'frame_id': msg.header.frame_id,
            'status': inv_status[msg.status],
            'status_reason': msg.status_reason,
            'lane_offset_m': float(msg.lane_offset_m),
            'traffic_light': inv_light[msg.traffic_light],
            'direction_sign': inv_sign[msg.direction_sign],
        }
    except KeyError as error:
        raise ConversionError(f'неизвестное значение enum: {error}') from error
    for field, flag in DISTANCES:
        scene[field] = float(getattr(msg, field)) if getattr(msg, flag) else None
    scene['confidence'] = float(msg.confidence)
    scene['source'] = msg.source
    return scene
