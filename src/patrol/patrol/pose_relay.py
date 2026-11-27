"""Нода pose_relay: ретранслирует позу turtlesim в sensor_pose с QoS best_effort."""

from typing import Optional

from patrol.qos import sensor_profile
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim_msgs.msg import Pose


class PoseRelay(Node):
    """Читает pose (надёжно) и публикует копию в sensor_pose как сенсор (best_effort)."""

    def __init__(self) -> None:
        super().__init__('pose_relay')
        # Относительные имена: в пространстве имён /robot_a выход — /robot_a/sensor_pose,
        # вход pose переназначается в launch на глобальный /turtle1/pose.
        self._pub = self.create_publisher(Pose, 'sensor_pose', sensor_profile('best_effort'))
        self._sub = self.create_subscription(Pose, 'pose', self._on_pose, 10)
        self._count = 0
        self.get_logger().info(
            f'pose_relay: {self._sub.topic_name} -> {self._pub.topic_name} (best_effort)')

    def _on_pose(self, msg: Pose) -> None:
        """Переслать позу без изменений."""
        self._pub.publish(msg)
        self._count += 1


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run patrol pose_relay."""
    rclpy.init(args=args)
    node = PoseRelay()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
