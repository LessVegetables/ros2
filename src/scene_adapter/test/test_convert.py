"""ПР10: round-trip JSON → SceneDescription.msg → JSON (null, все enum, метка времени)."""

import json
from pathlib import Path

import pytest
from robotics_course_interfaces.msg import SceneDescription
from scene_adapter.convert import ConversionError, from_msg, stamp_parts, to_msg
from scene_adapter.core import canonical_unknown

FIXTURES = Path(__file__).resolve().parents[3] / 'fixtures' / 'vlm'


def base() -> dict:
    return json.loads((FIXTURES / 'scene-clear.json').read_text(encoding='utf-8'))


def assert_same(a: dict, b: dict) -> None:
    assert set(a) == set(b)
    for key, value in a.items():
        if isinstance(value, float):
            assert b[key] == pytest.approx(value, abs=1e-6), key
        else:
            assert b[key] == value, key


def test_clear_round_trip() -> None:
    scene = base()
    assert_same(scene, from_msg(to_msg(scene)))


@pytest.mark.parametrize('light', ['none', 'red', 'yellow', 'green', 'unknown'])
@pytest.mark.parametrize('sign', ['none', 'left', 'right', 'straight', 'unknown'])
def test_all_enums_round_trip(light: str, sign: str) -> None:
    scene = dict(base(), traffic_light=light, direction_sign=sign)
    assert_same(scene, from_msg(to_msg(scene)))


def test_enum_codes() -> None:
    msg = to_msg(dict(base(), traffic_light='unknown', direction_sign='left'))
    assert msg.traffic_light == SceneDescription.LIGHT_UNKNOWN == 255
    assert msg.direction_sign == SceneDescription.SIGN_LEFT == 1


def test_null_distances_become_has_false() -> None:
    msg = to_msg(base())
    assert msg.has_stop_line and msg.stop_line_distance_m == pytest.approx(2.4)
    assert not msg.has_obstacle and msg.obstacle_distance_m == 0.0
    assert from_msg(msg)['obstacle_distance_m'] is None


def test_unknown_round_trip() -> None:
    scene = canonical_unknown(base(), 'low_confidence', 'mock')
    msg = to_msg(scene)
    assert msg.status == SceneDescription.STATUS_UNKNOWN and msg.status_reason == 'low_confidence'
    assert_same(scene, from_msg(msg))


@pytest.mark.parametrize('stamp,parts', [(0.0, (0, 0)), (1.0, (1, 0)), (12.25, (12, 250000000)),
                                         (3.9999999999, (4, 0))])
def test_stamp_split(stamp: float, parts: tuple) -> None:
    assert stamp_parts(stamp) == parts


def test_stamp_round_trip_and_frame() -> None:
    scene = dict(base(), stamp_s=12.25, frame_id='base_link')
    msg = to_msg(scene)
    assert (msg.header.stamp.sec, msg.header.stamp.nanosec) == (12, 250000000)
    assert msg.header.frame_id == 'base_link'
    assert from_msg(msg)['stamp_s'] == pytest.approx(12.25)


def test_unknown_enum_is_adapter_error() -> None:
    with pytest.raises(ConversionError):
        to_msg(dict(base(), traffic_light='purple'))
