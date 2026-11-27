#!/usr/bin/env python3
"""
ПР08: измерить доступность map→odom и медиану ковариации /amcl_pose.

Запускать до ros2 bag play: t0 — первый принятый /clock. Окно [t0+10; t0+30) по
времени симуляции; каждые 0,1 с один lookup_transform('map', 'odom', Time()).
Результат пишется в JSON (параметр output) — только измеренные значения.
"""

import json
import math
from pathlib import Path
from statistics import median
import sys
from typing import Optional

WARMUP_S = 10.0
WINDOW_S = 20.0
PERIOD_S = 0.1


def xy_covariance(cov: list) -> float:
    """Сумма элементов 0 и 7 ковариации позы (дисперсии x и y), м²."""
    return float(cov[0]) + float(cov[7])


def in_window(t: float, t0: float, warmup_s: float = WARMUP_S,
              window_s: float = WINDOW_S) -> bool:
    """t принадлежит [t0 + warmup, t0 + warmup + window)."""
    return t0 + warmup_s <= t < t0 + warmup_s + window_s


def slot_index(t: float, t0: float, warmup_s: float = WARMUP_S,
               period_s: float = PERIOD_S) -> int:
    """Номер шага 0,1 с внутри окна (0…199)."""
    return int(math.floor((t - t0 - warmup_s) / period_s + 1e-9))


def summarize(successes: int, total: int, covariances: list) -> dict:
    """Итог окна: доля успешных запросов и медиана ковариации."""
    return {
        'tf_queries_total': total,
        'tf_queries_successful': successes,
        'tf_availability': successes / total if total else 0.0,
        'amcl_pose_samples': len(covariances),
        'median_xy_covariance_m2': median(covariances) if covariances else None,
    }


def main(argv: Optional[list] = None) -> None:
    """ROS-нода измерения (импорт rclpy только здесь, чтобы тесты шли без ROS)."""
    import rclpy
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from rclpy.time import Time
    from rosgraph_msgs.msg import Clock
    from tf2_ros import Buffer, TransformListener
    from tf2_ros import TransformException

    class Measure(Node):

        def __init__(self) -> None:
            super().__init__('measure_localization',
                             parameter_overrides=[])
            self.declare_parameter('output', 'localization-metrics.json')
            self.t0: Optional[float] = None
            self.last_clock: Optional[float] = None
            self.time_went_back = False
            self.done = False
            self.slots: dict = {}
            self.covs: list = []
            self.buffer = Buffer()
            self.listener = TransformListener(self.buffer, self)
            self.create_subscription(Clock, '/clock', self.on_clock, 100)
            self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.on_pose, 50)
            self.first_error: Optional[str] = None
            self.get_logger().info('готов: жду первый /clock (запустите ros2 bag play)')

        def now_s(self) -> float:
            return self.get_clock().now().nanoseconds * 1e-9

        def on_clock(self, msg: Clock) -> None:
            t = msg.clock.sec + msg.clock.nanosec * 1e-9
            if self.t0 is None:
                self.t0 = t
                self.get_logger().info(f't0 = {t:.3f} с (первый /clock)')
            if self.last_clock is not None and t < self.last_clock:
                self.time_went_back = True
            self.last_clock = t
            if self.done:
                return
            if in_window(t, self.t0):
                slot = slot_index(t, self.t0)
                if slot not in self.slots:
                    try:
                        self.buffer.lookup_transform('map', 'odom', Time())
                        self.slots[slot] = True
                    except TransformException as error:
                        self.slots[slot] = False
                        if self.first_error is None:
                            self.first_error = str(error)
                            self.get_logger().warning(f'map→odom недоступно: {error}')
            elif t >= self.t0 + WARMUP_S + WINDOW_S:
                self.finish()

        def on_pose(self, msg: PoseWithCovarianceStamped) -> None:
            if self.t0 is None or self.done:
                return
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if in_window(stamp, self.t0):
                self.covs.append(xy_covariance(msg.pose.covariance))

        def finish(self) -> None:
            self.done = True
            total = int(WINDOW_S / PERIOD_S)
            successes = sum(1 for ok in self.slots.values() if ok)
            result = summarize(successes, total, self.covs)
            result.update({
                't0_s': self.t0,
                'warmup_s': WARMUP_S,
                'duration_s': WINDOW_S,
                'slots_observed': len(self.slots),
                'time_went_back': self.time_went_back,
                'first_tf_error': self.first_error,
            })
            path = Path(str(self.get_parameter('output').value))
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n',
                            encoding='utf-8')
            self.get_logger().info(f'метрики записаны в {path}: {json.dumps(result)}')

    rclpy.init(args=argv)
    node = Measure()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if not node.done and node.t0 is not None:
            node.get_logger().warning('окно не завершено: запись закончилась раньше?')
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main(sys.argv)
