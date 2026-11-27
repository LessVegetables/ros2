"""ПР09: чистые функции — байты Image, детектор, проекция, проверка пары."""

import struct

from perception_baseline.core import (depth16_values, detect, pair_problem, project,
                                      rgb8_pixels)
import pytest

CONFIG = {'channel_order': 'rgb', 'red_min': 180, 'green_max': 120, 'blue_max': 120,
          'min_area_px': 2}
CALIB = {'fx': 8.0, 'fy': 8.0, 'cx': 3.5, 'cy': 2.5, 'depth_scale_m': 0.001}
META = {'stamp': (5, 0), 'frame_id': 'camera_optical_frame', 'width': 8, 'height': 6,
        'encoding': 'rgb8'}


def image_with_red(x0: int, y0: int, w: int, h: int) -> list:
    return [(255, 0, 0) if x0 <= i % 8 < x0 + w and y0 <= i // 8 < y0 + h else (40, 40, 40)
            for i in range(48)]


def test_step_padding_respected() -> None:
    row = bytes([1, 2, 3] * 8) + b'\xff\xff'      # step=26: 2 байта выравнивания
    pixels = rgb8_pixels(8, 2, 26, row * 2)
    assert len(pixels) == 16 and pixels[8] == (1, 2, 3)


def test_depth_endianness() -> None:
    le = b''.join(struct.pack('<H', 1000) for _ in range(48))
    be = b''.join(struct.pack('>H', 1000) for _ in range(48))
    assert depth16_values(8, 6, 16, le, False)[0] == 1000
    assert depth16_values(8, 6, 16, be, True)[0] == 1000


def test_detect_box() -> None:
    assert detect(8, 6, image_with_red(2, 2, 2, 2), CONFIG) == [[2, 2, 2, 2]]


def test_single_pixel_below_min_area() -> None:
    assert detect(8, 6, image_with_red(0, 0, 1, 1), CONFIG) == []


def test_projection_formula() -> None:
    point = project([2, 2, 2, 2], [1000] * 48, 8, CALIB)
    assert point['status'] == 'ok' and (point['u'], point['v']) == (3, 3)
    assert point['x_m'] == pytest.approx(-0.0625)
    assert point['y_m'] == pytest.approx(0.0625)
    assert point['z_m'] == pytest.approx(1.0)


def test_zero_and_missing_depth_unknown() -> None:
    assert project([2, 2, 2, 2], [0] * 48, 8, CALIB) == {'status': 'unknown',
                                                         'reason': 'zero_depth'}
    assert project([2, 2, 2, 2], None, 8, CALIB)['reason'] == 'missing_depth'


@pytest.mark.parametrize('change,reason', [
    ({'stamp': (4, 0)}, 'stamp_mismatch'),
    ({'frame_id': 'camera_link'}, 'frame_mismatch'),
    ({'encoding': '32FC1'}, 'invalid_depth'),
    ({'width': 4}, 'invalid_depth'),
])
def test_pair_problems(change: dict, reason: str) -> None:
    depth = dict(META, encoding='16UC1', **{k: v for k, v in change.items() if k != 'encoding'})
    if 'encoding' in change:
        depth['encoding'] = change['encoding']
    assert pair_problem(META, depth, 'camera_optical_frame') == reason


def test_good_pair() -> None:
    assert pair_problem(META, dict(META, encoding='16UC1'), 'camera_optical_frame') is None
    assert pair_problem(META, None, 'camera_optical_frame') == 'missing_depth'
