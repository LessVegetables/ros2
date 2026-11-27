"""ПР09: ROS-тест ноды — сообщения из fixture, ответы по топикам (4 случая + frame)."""

import itertools
from pathlib import Path
import time

from diagnostic_msgs.msg import DiagnosticArray
from perception_baseline.fixture_io import depth_msg, read_pgm, rgb_msg
from perception_baseline.node import PerceptionBaseline
import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection3DArray

FIXTURE = Path(__file__).resolve().parent / 'data'
FRAME = 'camera_optical_frame'
# Свой домен на каждый тест: сообщения прошлого теста не попадут в следующий.
_DOMAINS = itertools.count(150)


@pytest.fixture
def system():
    rclpy.init(domain_id=next(_DOMAINS))
    node = PerceptionBaseline()
    tester = rclpy.create_node('perception_tester')
    got: dict = {'2d': [], '3d': [], 'status': []}
    tester.create_subscription(Detection2DArray, '/perception/detections_2d',
                               lambda m: got['2d'].append(m), 10)
    tester.create_subscription(Detection3DArray, '/perception/objects_3d',
                               lambda m: got['3d'].append(m), 10)
    tester.create_subscription(DiagnosticArray, '/perception/status',
                               lambda m: got['status'].append(m), 10)
    rgb_pub = tester.create_publisher(Image, '/camera/image_raw', qos_profile_sensor_data)
    depth_pub = tester.create_publisher(Image, '/camera/depth/image_raw', qos_profile_sensor_data)
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    executor.add_node(tester)

    def spin(seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.02)

    def send(mode: str):
        spin(0.5)
        stamp = tester.get_clock().now().to_msg()
        rgb = rgb_msg(FIXTURE / 'sample-01.ppm', stamp, FRAME)
        w, h, values = read_pgm(FIXTURE / 'constant-1m.pgm')
        if mode == 'zero_depth':
            values = [0] * len(values)
        depth = depth_msg(w, h, values, stamp, FRAME)
        if mode == 'stamp_mismatch':
            depth.header.stamp.sec -= 1
        if mode == 'frame_mismatch':
            depth.header.frame_id = 'camera_link'
        if mode != 'no_depth':
            depth_pub.publish(depth)
            spin(0.1)
        rgb_pub.publish(rgb)
        spin(1.0)
        return stamp

    yield send, got
    executor.shutdown()
    node.destroy_node()
    tester.destroy_node()
    rclpy.try_shutdown()


def reason(status: DiagnosticArray) -> str:
    return {kv.key: kv.value for kv in status.status[0].values}['reason']


def test_valid_pair_gives_projected_point(system) -> None:
    send, got = system
    stamp = send('ok')
    assert got['2d'] and got['3d'] and got['status']
    d3 = got['3d'][-1]
    assert d3.header.stamp == stamp and d3.header.frame_id == FRAME
    assert got['2d'][-1].header.stamp == stamp
    p = d3.detections[0].bbox.center.position
    assert (p.x, p.y, p.z) == pytest.approx((-0.0625, 0.0625, 1.0))
    assert d3.detections[0].results[0].pose.pose.position.z == pytest.approx(1.0)
    assert d3.detections[0].bbox.size.x == 0.0
    assert got['status'][-1].status[0].level == b'\x00'


@pytest.mark.parametrize('mode', ['zero_depth', 'no_depth', 'stamp_mismatch',
                                  'frame_mismatch'])
def test_unknown_keeps_2d_without_invented_3d(system, mode: str) -> None:
    send, got = system
    stamp = send(mode)
    assert len(got['2d'][-1].detections) == 1, 'корректная 2D-детекция сохраняется'
    assert got['3d'][-1].detections == [], 'нет выдуманной 3D-точки'
    assert got['3d'][-1].header.stamp == stamp
    status = got['status'][-1]
    assert status.status[0].level == b'\x01'
    expected = 'missing_depth' if mode == 'no_depth' else mode
    assert reason(status) == expected
