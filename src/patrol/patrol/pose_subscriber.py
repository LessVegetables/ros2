"""Нода pose_subscriber: подписчик sensor_pose с настраиваемой надёжностью QoS."""

from typing import Optional

from patrol.qos import sensor_profile
import rclpy
from rclpy.event_handler import QoSRequestedIncompatibleQoSInfo, SubscriptionEventCallbacks
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim_msgs.msg import Pose


class PoseSubscriber(Node):
    """Считает полученные позы; сообщает о несовместимом QoS издателя."""

    def __init__(self) -> None:
        super().__init__('pose_subscriber')
        self.declare_parameter('reliability', 'best_effort')
        reliability = str(self.get_parameter('reliability').value)
        events = SubscriptionEventCallbacks(incompatible_qos=self._on_incompatible)
        self._sub = self.create_subscription(
            Pose, 'sensor_pose', self._on_pose, sensor_profile(reliability),
            event_callbacks=events)
        self._count = 0
        self.get_logger().info(f'pose_subscriber: {self._sub.topic_name}, {reliability}')

    def _on_pose(self, msg: Pose) -> None:
        """Посчитать сообщение и иногда напечатать его."""
        self._count += 1
        if self._count == 1 or self._count % 20 == 0:
            self.get_logger().info(
                f'count={self._count} x={msg.x:.2f} y={msg.y:.2f} theta={msg.theta:.2f}')

    def _on_incompatible(self, event: QoSRequestedIncompatibleQoSInfo) -> None:
        """Сообщить, что издатель не может обслужить запрошенный профиль."""
        self.get_logger().warning(
            f'несовместимый QoS с издателем: total_count={event.total_count}, '
            f'last_policy_kind={event.last_policy_kind}')


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run patrol pose_subscriber."""
    rclpy.init(args=args)
    node = PoseSubscriber()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
