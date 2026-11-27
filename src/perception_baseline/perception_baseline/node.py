"""Нода perception_baseline: RGB + совмещённая глубина → 2D/3D детекции и диагностика."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from ament_index_python.packages import get_package_share_directory
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from perception_baseline.core import (depth16_values, detect, pair_problem, project,
                                      rgb8_pixels)
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import (Detection2D, Detection2DArray, Detection3D, Detection3DArray,
                             ObjectHypothesisWithPose)

LABEL = 'cone'


def meta(msg: Image) -> dict[str, Any]:
    """Поля, по которым проверяется совместимость пары."""
    return {'stamp': (msg.header.stamp.sec, msg.header.stamp.nanosec),
            'frame_id': msg.header.frame_id, 'width': msg.width, 'height': msg.height,
            'encoding': msg.encoding}


class PerceptionBaseline(Node):
    """Получение сообщений отделено от вычисления (core.py)."""

    def __init__(self) -> None:
        super().__init__('perception_baseline')
        share = Path(get_package_share_directory('perception_baseline')) / 'config'
        self.declare_parameter('detector_config', str(share / 'baseline-detector.json'))
        self.declare_parameter('calibration', str(share / 'calibration.json'))
        self.declare_parameter('depth_wait_s', 0.3)
        self.config = json.loads(Path(self.get_parameter('detector_config').value).read_text())
        self.calib = json.loads(Path(self.get_parameter('calibration').value).read_text())
        self.frame = str(self.calib['frame_id'])
        self.depth_by_stamp: dict[tuple[int, int], Image] = {}
        self.pending: list[tuple[Image, Any]] = []
        self.create_subscription(Image, '/camera/depth/image_raw', self.on_depth,
                                 qos_profile_sensor_data)
        self.create_subscription(Image, '/camera/image_raw', self.on_rgb, qos_profile_sensor_data)
        self.pub2d = self.create_publisher(Detection2DArray, '/perception/detections_2d', 10)
        self.pub3d = self.create_publisher(Detection3DArray, '/perception/objects_3d', 10)
        self.pub_status = self.create_publisher(DiagnosticArray, '/perception/status', 10)
        self.create_timer(0.05, self.flush_pending)

    def on_depth(self, msg: Image) -> None:
        """Запомнить глубину по stamp (ограниченный буфер)."""
        self.depth_by_stamp[(msg.header.stamp.sec, msg.header.stamp.nanosec)] = msg
        while len(self.depth_by_stamp) > 20:
            self.depth_by_stamp.pop(next(iter(self.depth_by_stamp)))

    def on_rgb(self, msg: Image) -> None:
        """Обработать сразу, если пара уже есть; иначе ждать не дольше depth_wait_s."""
        key = (msg.header.stamp.sec, msg.header.stamp.nanosec)
        if key in self.depth_by_stamp:
            self.process(msg, self.depth_by_stamp.pop(key))
        else:
            self.pending.append((msg, self.get_clock().now()))

    def flush_pending(self) -> None:
        """По истечении ожидания: глубины нет или она другого времени."""
        wait = float(self.get_parameter('depth_wait_s').value)
        keep = []
        for rgb, since in self.pending:
            key = (rgb.header.stamp.sec, rgb.header.stamp.nanosec)
            if key in self.depth_by_stamp:
                self.process(rgb, self.depth_by_stamp.pop(key))
            elif (self.get_clock().now() - since).nanoseconds * 1e-9 >= wait:
                other = next(reversed(self.depth_by_stamp.values()), None)
                self.process(rgb, other)
            else:
                keep.append((rgb, since))
        self.pending = keep

    def process(self, rgb: Image, depth: Optional[Image]) -> None:
        """Вычислить и опубликовать 2D, 3D и диагностику с stamp RGB."""
        header = rgb.header
        problem = pair_problem(meta(rgb), meta(depth) if depth else None, self.frame)
        boxes: list[list[int]] = []
        reason = problem
        if rgb.encoding != 'rgb8':
            reason = 'invalid_rgb'
        else:
            pixels = rgb8_pixels(rgb.width, rgb.height, rgb.step, bytes(rgb.data))
            boxes = detect(rgb.width, rgb.height, pixels, self.config)
        values = None
        if reason is None and depth is not None:
            try:
                values = depth16_values(depth.width, depth.height, depth.step,
                                        bytes(depth.data), bool(depth.is_bigendian))
            except ValueError:
                reason = 'invalid_depth'
        out2d = Detection2DArray(header=header)
        out3d = Detection3DArray(header=header)
        reasons: list[str] = []
        for box in boxes:
            d2 = Detection2D(header=header)
            d2.bbox.center.position.x = box[0] + box[2] / 2.0
            d2.bbox.center.position.y = box[1] + box[3] / 2.0
            d2.bbox.size_x, d2.bbox.size_y = float(box[2]), float(box[3])
            hyp = ObjectHypothesisWithPose()
            hyp.hypothesis.class_id, hyp.hypothesis.score = LABEL, 1.0
            d2.results.append(hyp)
            out2d.detections.append(d2)
            point = (project(box, values, rgb.width, self.calib) if reason is None
                     else {'status': 'unknown', 'reason': reason})
            if point['status'] != 'ok':
                reasons.append(point['reason'])
                continue
            d3 = Detection3D(header=header)
            d3.bbox.center.position.x = point['x_m']
            d3.bbox.center.position.y = point['y_m']
            d3.bbox.center.position.z = point['z_m']
            hyp3 = ObjectHypothesisWithPose()
            hyp3.hypothesis.class_id, hyp3.hypothesis.score = LABEL, 1.0
            hyp3.pose.pose.position = d3.bbox.center.position
            d3.results.append(hyp3)
            out3d.detections.append(d3)
        if not boxes and reason:
            reasons.append(reason)
        self.pub2d.publish(out2d)
        self.pub3d.publish(out3d)
        self.pub_status.publish(self.status(header, len(boxes), len(out3d.detections), reasons))

    def status(self, header: Any, n2d: int, n3d: int, reasons: list[str]) -> DiagnosticArray:
        """OK, если есть 3D-точки; WARN с reason, если пространственный результат неизвестен."""
        st = DiagnosticStatus(name='perception_baseline', hardware_id=self.frame)
        if n3d > 0 and not reasons:
            st.level, st.message = DiagnosticStatus.OK, 'spatial_ok'
        elif n2d == 0 and not reasons:
            st.level, st.message = DiagnosticStatus.OK, 'no_detections'
        else:
            st.level, st.message = DiagnosticStatus.WARN, reasons[0] if reasons else 'unknown'
        st.values = [
            KeyValue(key='reason', value=reasons[0] if reasons else ''),
            KeyValue(key='stamp', value=f'{header.stamp.sec}.{header.stamp.nanosec:09d}'),
            KeyValue(key='frame_id', value=self.frame),
            KeyValue(key='detections_2d', value=str(n2d)),
            KeyValue(key='objects_3d', value=str(n3d)),
            KeyValue(key='geometry', value='точка поверхности на луче центра bbox; '
                     'bbox.size=0: размер и ориентация не оцениваются'),
        ]
        return DiagnosticArray(header=header, status=[st])


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run perception_baseline perception_baseline."""
    rclpy.init(args=args)
    node = PerceptionBaseline()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
