"""
Чистая логика ПР09 без rclpy: тот же baseline, что в evaluate_perception.py.

Алгоритм поиска красных связных областей и формула проекции повторяют публичный
evaluator из course kit (tools/evaluate_perception.py, v1-w12), но работают с
байтами sensor_msgs/Image, а не с файлами.
"""

from __future__ import annotations

import math
import struct
from typing import Any, Optional, Sequence

Pixel = tuple[int, int, int]
Box = list[int]

REASONS = ('missing_depth', 'zero_depth', 'stamp_mismatch', 'frame_mismatch', 'invalid_depth')


def rgb8_pixels(width: int, height: int, step: int, data: bytes) -> list[Pixel]:
    """Байты rgb8 c учётом step (строка может быть длиннее width*3)."""
    if step < width * 3 or len(data) < step * height:
        raise ValueError('rgb8: step или размер data не согласованы с width/height')
    pixels: list[Pixel] = []
    for row in range(height):
        base = row * step
        for col in range(width):
            i = base + col * 3
            pixels.append((data[i], data[i + 1], data[i + 2]))
    return pixels


def depth16_values(width: int, height: int, step: int, data: bytes,
                   is_bigendian: bool) -> list[int]:
    """Байты 16UC1 (мм) c учётом step и порядка байт."""
    if step < width * 2 or len(data) < step * height:
        raise ValueError('16UC1: step или размер data не согласованы с width/height')
    fmt = '>H' if is_bigendian else '<H'
    values: list[int] = []
    for row in range(height):
        base = row * step
        for col in range(width):
            values.append(struct.unpack_from(fmt, data, base + col * 2)[0])
    return values


def detect(width: int, height: int, pixels: Sequence[Pixel], config: dict[str, Any]) -> list[Box]:
    """Красные связные области (4-связность) площадью ≥ min_area_px → bbox [x, y, w, h]."""
    if config.get('channel_order') != 'rgb':
        raise ValueError('baseline принимает только RGB; проверьте channel_order')
    red_min, green_max, blue_max = (int(config[k]) for k in ('red_min', 'green_max', 'blue_max'))
    mask = {i for i, (r, g, b) in enumerate(pixels)
            if r >= red_min and g <= green_max and b <= blue_max}
    boxes: list[Box] = []
    while mask:
        stack = [mask.pop()]
        component: list[int] = []
        while stack:
            index = stack.pop()
            component.append(index)
            x, y = index % width, index // width
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                neighbour = ny * width + nx
                if 0 <= nx < width and 0 <= ny < height and neighbour in mask:
                    mask.remove(neighbour)
                    stack.append(neighbour)
        if len(component) >= int(config['min_area_px']):
            xs = [i % width for i in component]
            ys = [i // width for i in component]
            boxes.append([min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1])
    return sorted(boxes)


def project(box: Box, depth: Optional[Sequence[int]], width: int,
            calibration: dict[str, Any]) -> dict[str, Any]:
    """Точка поверхности на луче центрального пикселя bbox в camera_optical_frame."""
    if depth is None:
        return {'status': 'unknown', 'reason': 'missing_depth'}
    u, v = box[0] + box[2] // 2, box[1] + box[3] // 2
    raw = depth[v * width + u]
    if raw == 0:
        return {'status': 'unknown', 'reason': 'zero_depth'}
    z = raw * float(calibration['depth_scale_m'])
    if not math.isfinite(z) or z <= 0:
        return {'status': 'unknown', 'reason': 'invalid_depth'}
    return {
        'status': 'ok', 'u': u, 'v': v,
        'x_m': (u - float(calibration['cx'])) * z / float(calibration['fx']),
        'y_m': (v - float(calibration['cy'])) * z / float(calibration['fy']),
        'z_m': z,
    }


def pair_problem(rgb: dict[str, Any], depth: Optional[dict[str, Any]],
                 expected_frame: str) -> Optional[str]:
    """
    Причина, по которой пару RGB/depth нельзя совместить, или None.

    rgb/depth: {'stamp': (sec, nanosec), 'frame_id', 'width', 'height', 'encoding'}.
    """
    if rgb['frame_id'] != expected_frame:
        return 'frame_mismatch'
    if depth is None:
        return 'missing_depth'
    if depth['frame_id'] != expected_frame:
        return 'frame_mismatch'
    if depth['stamp'] != rgb['stamp']:
        return 'stamp_mismatch'
    if (depth['encoding'] != '16UC1' or depth['width'] != rgb['width']
            or depth['height'] != rgb['height']):
        return 'invalid_depth'
    return None
