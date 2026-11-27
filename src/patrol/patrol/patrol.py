"""Нода patrol: подписка на позу turtlesim и таймер, публикующий Twist в cmd_vel."""

from typing import Optional

from geometry_msgs.msg import Twist
from patrol.command import choose_command
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.publisher import Publisher
from rclpy.subscription import Subscription
from rclpy.timer import Timer
from turtlesim_msgs.msg import Pose

PERIOD_S = 0.1
"""Период таймера команды: 0,1 с, то есть 10 Гц."""


class Patrol(Node):
    """Хранит последнюю позу и по таймеру публикует команду скорости."""

    def __init__(self) -> None:
        super().__init__('patrol')
        self._last_pose: Optional[Pose] = None
        # Подписка хранится в поле: без ссылки объект удалил бы сборщик мусора.
        self._pose_sub: Subscription = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10)
        # Относительное имя: без remap это /cmd_vel, а не /turtle1/cmd_vel.
        self._cmd_pub: Publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer: Timer = self.create_timer(PERIOD_S, self._on_timer)
        self.get_logger().info(
            f'patrol: поза из /turtle1/pose, команда в '
            f'{self._cmd_pub.topic_name} каждые {PERIOD_S} с')

    def _on_pose(self, msg: Pose) -> None:
        """Сохранить последнюю позу (callback подписки, больше ничего не делает)."""
        self._last_pose = msg

    def _on_timer(self) -> None:
        """Выбрать команду по последней позе и опубликовать её (callback таймера)."""
        command = choose_command(self._last_pose)
        msg = Twist()
        msg.linear.x = command.linear_x
        msg.angular.z = command.angular_z
        self._cmd_pub.publish(msg)


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run patrol patrol."""
    rclpy.init(args=args)
    node = Patrol()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
