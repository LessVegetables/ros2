"""Тестовый источник: AckermannDriveStamped в /drive/safe со свежим stamp из /clock."""

from typing import Optional

from ackermann_msgs.msg import AckermannDriveStamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class DriveSource(Node):
    """Публикует постоянную команду с частотой rate_hz по времени симуляции."""

    def __init__(self) -> None:
        super().__init__('drive_source')
        self.declare_parameter('speed', 0.5)
        self.declare_parameter('steering_angle', 0.0)
        self.declare_parameter('rate_hz', 10.0)
        self._pub = self.create_publisher(AckermannDriveStamped, '/drive/safe', 10)
        self.create_timer(1.0 / float(self.get_parameter('rate_hz').value), self._tick)

    def _tick(self) -> None:
        """Отправить команду со stamp текущих ROS-часов (use_sim_time → /clock)."""
        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.drive.speed = float(self.get_parameter('speed').value)
        msg.drive.steering_angle = float(self.get_parameter('steering_angle').value)
        self._pub.publish(msg)


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run course_simulation drive_source."""
    rclpy.init(args=args)
    node = DriveSource()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
