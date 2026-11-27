"""Нода odom_adapter: /vehicle/odom_gz → /vehicle/odom и единственный tf odom→base_link."""

from typing import Optional

from course_simulation.drive_logic import all_finite, strip_gz_prefix
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


def normalize(msg: Odometry) -> Optional[Odometry]:
    """Снять префикс course_ackermann/ c frames; stamp, pose, twist и covariance сохраняются."""
    parent = strip_gz_prefix(msg.header.frame_id)
    child = strip_gz_prefix(msg.child_frame_id)
    if parent != 'odom' or child != 'base_link':
        return None
    p, q = msg.pose.pose.position, msg.pose.pose.orientation
    t = msg.twist.twist
    values = [p.x, p.y, p.z, q.x, q.y, q.z, q.w, t.linear.x, t.linear.y, t.linear.z,
              t.angular.x, t.angular.y, t.angular.z,
              *msg.pose.covariance, *msg.twist.covariance]
    if not all_finite([float(v) for v in values]):
        return None
    out = Odometry()
    out.header.stamp = msg.header.stamp
    out.header.frame_id = parent
    out.child_frame_id = child
    out.pose = msg.pose
    out.twist = msg.twist
    return out


def to_transform(odom: Odometry) -> TransformStamped:
    """Тот же stamp и поза в виде odom→base_link."""
    tf = TransformStamped()
    tf.header = odom.header
    tf.child_frame_id = odom.child_frame_id
    tf.transform.translation.x = odom.pose.pose.position.x
    tf.transform.translation.y = odom.pose.pose.position.y
    tf.transform.translation.z = odom.pose.pose.position.z
    tf.transform.rotation = odom.pose.pose.orientation
    return tf


class OdomAdapter(Node):
    """Публикует нормализованную одометрию и динамическую связь odom→base_link."""

    def __init__(self) -> None:
        super().__init__('odom_adapter')
        self._pub = self.create_publisher(Odometry, '/vehicle/odom', 10)
        self._sub = self.create_subscription(Odometry, '/vehicle/odom_gz', self._on_odom, 10)
        self._tf = TransformBroadcaster(self)
        self._rejected = 0

    def _on_odom(self, msg: Odometry) -> None:
        """Нормализовать или отклонить сообщение."""
        odom = normalize(msg)
        if odom is None:
            self._rejected += 1
            if self._rejected == 1 or self._rejected % 100 == 0:
                self.get_logger().warning(
                    f'одометрия отклонена ({self._rejected}): frames '
                    f'{msg.header.frame_id!r}->{msg.child_frame_id!r} или нечисловые значения')
            return
        self._pub.publish(odom)
        self._tf.sendTransform(to_transform(odom))


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run course_simulation odom_adapter."""
    rclpy.init(args=args)
    node = OdomAdapter()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
