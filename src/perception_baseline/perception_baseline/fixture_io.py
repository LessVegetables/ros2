"""Чтение текстовых PPM/PGM fixture ПР09 и сборка sensor_msgs/Image."""

from __future__ import annotations

from pathlib import Path
import struct
from typing import Any

from builtin_interfaces.msg import Time
from sensor_msgs.msg import Image


def _tokens(path: Path) -> list[str]:
    tokens: list[str] = []
    for line in Path(path).read_text(encoding='ascii').splitlines():
        tokens.extend(line.split('#', 1)[0].split())
    return tokens


def read_ppm(path: Path) -> tuple[int, int, bytes]:
    """P3 → (width, height, плотные байты rgb8)."""
    t = _tokens(path)
    assert t[0] == 'P3', path
    width, height = int(t[1]), int(t[2])
    return width, height, bytes(int(v) for v in t[4:4 + width * height * 3])


def read_pgm(path: Path) -> tuple[int, int, list[int]]:
    """P2 → (width, height, значения глубины в мм)."""
    t = _tokens(path)
    assert t[0] == 'P2', path
    width, height = int(t[1]), int(t[2])
    return width, height, [int(v) for v in t[4:4 + width * height]]


def rgb_msg(path: Path, stamp: Any, frame_id: str) -> Image:
    """rgb8, step = width·3."""
    width, height, data = read_ppm(path)
    msg = Image(height=height, width=width, encoding='rgb8', is_bigendian=0, step=width * 3)
    # Копия stamp: иначе RGB и depth делят один объект Time.
    msg.header.stamp = Time(sec=stamp.sec, nanosec=stamp.nanosec)
    msg.header.frame_id = frame_id
    msg.data = data
    return msg


def depth_msg(width: int, height: int, values: list[int], stamp: Any, frame_id: str) -> Image:
    """16UC1 little-endian, step = width·2."""
    msg = Image(height=height, width=width, encoding='16UC1', is_bigendian=0, step=width * 2)
    msg.header.stamp = Time(sec=stamp.sec, nanosec=stamp.nanosec)
    msg.header.frame_id = frame_id
    msg.data = b''.join(struct.pack('<H', v) for v in values)
    return msg
