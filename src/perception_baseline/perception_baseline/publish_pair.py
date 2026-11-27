"""
Отправить пару RGB/depth из fixture ПР09 (depth публикуется раньше RGB).

ros2 run perception_baseline publish_pair --ros-args -p fixture:=<.course-kit/v1/fixtures/pr09>
-p sample:=sample-01 -p mode:=ok|zero_depth|no_depth|stamp_mismatch|frame_mismatch
"""

from pathlib import Path
import time
from typing import Optional

from perception_baseline.fixture_io import depth_msg, read_pgm, rgb_msg
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

MODES = ('ok', 'zero_depth', 'no_depth', 'stamp_mismatch', 'frame_mismatch')


def main(args: Optional[list[str]] = None) -> None:
    """Опубликовать одну пару и завершиться."""
    rclpy.init(args=args)
    node = Node('publish_pair')
    fixture = Path(node.declare_parameter('fixture', '.course-kit/v1/fixtures/pr09').value)
    sample = node.declare_parameter('sample', 'sample-01').value
    mode = node.declare_parameter('mode', 'ok').value
    if mode not in MODES:
        raise SystemExit(f'mode должен быть одним из {MODES}')
    rgb_pub = node.create_publisher(Image, '/camera/image_raw', qos_profile_sensor_data)
    depth_pub = node.create_publisher(Image, '/camera/depth/image_raw', qos_profile_sensor_data)
    time.sleep(1.5)  # дать подписчикам обнаружить издателей
    stamp = node.get_clock().now().to_msg()
    rgb = rgb_msg(fixture / 'images' / f'{sample}.ppm', stamp, 'camera_optical_frame')
    width, height, values = read_pgm(fixture / 'depth' / 'constant-1m.pgm')
    if mode == 'zero_depth':
        values = [0] * len(values)
    depth = depth_msg(width, height, values, stamp, 'camera_optical_frame')
    if mode == 'stamp_mismatch':
        depth.header.stamp.sec -= 1
    if mode == 'frame_mismatch':
        depth.header.frame_id = 'camera_link'
    if mode != 'no_depth':
        depth_pub.publish(depth)
        time.sleep(0.05)
    rgb_pub.publish(rgb)
    node.get_logger().info(f'отправлено: {sample}, mode={mode}, stamp={stamp.sec}.{stamp.nanosec}')
    time.sleep(0.5)
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()
