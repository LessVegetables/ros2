"""Нода drive_adapter: /drive/safe (AckermannDriveStamped) → /vehicle/gz_cmd_vel (Twist)."""

from typing import Optional

from ackermann_msgs.msg import AckermannDriveStamped
from course_simulation.drive_logic import drive_to_twist
from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rclpy.time import Time


class DriveAdapter(Node):
    """Переводит безопасную команду Ackermann в Twist для моста ros_gz."""

    def __init__(self) -> None:
        super().__init__('drive_adapter')
        self.declare_parameter('input_topic', '/drive/safe')
        self.declare_parameter('output_topic', '/vehicle/gz_cmd_vel')
        self.declare_parameter('max_age_s', 0.25)
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        self._pub = self.create_publisher(
            Twist, self.get_parameter('output_topic').value, qos)
        self._sub = self.create_subscription(
            AckermannDriveStamped, self.get_parameter('input_topic').value,
            self._on_drive, qos)
        self._last_reason = ''

    def _on_drive(self, msg: AckermannDriveStamped) -> None:
        """Проверить и перевести команду; при отказе — нулевой Twist."""
        age = (self.get_clock().now() - Time.from_msg(msg.header.stamp)).nanoseconds * 1e-9
        command, reason = drive_to_twist(
            float(msg.drive.speed), float(msg.drive.steering_angle), age,
            float(self.get_parameter('max_age_s').value))
        out = Twist()
        out.linear.x = command.linear_x
        out.angular.z = command.angular_z
        self._pub.publish(out)
        if reason and reason != self._last_reason:
            self.get_logger().warning(f'команда отклонена: {reason} (age={age:.3f} с)')
        self._last_reason = reason


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run course_simulation drive_adapter."""
    rclpy.init(args=args)
    node = DriveAdapter()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
