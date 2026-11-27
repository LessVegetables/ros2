"""Нода patrol: подписка на позу turtlesim и таймер, публикующий Twist в cmd_vel."""

from typing import Optional

from geometry_msgs.msg import Twist
from patrol.command import (
    choose_command, LINEAR_SPEED, period_for, PUBLISH_HZ, TURN_RATE, validate_parameter,
)
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.publisher import Publisher
from rclpy.subscription import Subscription
from rclpy.timer import Timer
from turtlesim_msgs.msg import Pose


class Patrol(Node):
    """Хранит последнюю позу и по таймеру публикует команду скорости."""

    def __init__(self) -> None:
        super().__init__('patrol')
        self.declare_parameter('linear_speed', LINEAR_SPEED)
        self.declare_parameter('turn_rate', TURN_RATE)
        self.declare_parameter('publish_hz', PUBLISH_HZ)
        # Значения из командной строки (-p) проходят ту же проверку, что и param set.
        for name in ('linear_speed', 'turn_rate', 'publish_hz'):
            reason = validate_parameter(name, self.get_parameter(name).value)
            if reason is not None:
                raise ValueError(reason)
        self._linear_speed = float(self.get_parameter('linear_speed').value)
        self._turn_rate = float(self.get_parameter('turn_rate').value)
        self._publish_hz = float(self.get_parameter('publish_hz').value)

        self._last_pose: Optional[Pose] = None
        # Подписка хранится в поле: без ссылки объект удалил бы сборщик мусора.
        self._pose_sub: Subscription = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10)
        # Относительное имя: без remap это /cmd_vel, а не /turtle1/cmd_vel.
        self._cmd_pub: Publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer: Timer = self.create_timer(period_for(self._publish_hz), self._on_timer)

        # Сначала проверка (можно отказать), затем применение уже принятых значений.
        self.add_on_set_parameters_callback(self._on_set_parameters)
        self.add_post_set_parameters_callback(self._on_parameters_set)
        self.get_logger().info(
            f'patrol: поза из /turtle1/pose, команда в {self._cmd_pub.topic_name}, '
            f'linear_speed={self._linear_speed}, turn_rate={self._turn_rate}, '
            f'publish_hz={self._publish_hz}')

    def _on_pose(self, msg: Pose) -> None:
        """Сохранить последнюю позу (callback подписки, больше ничего не делает)."""
        self._last_pose = msg

    def _on_timer(self) -> None:
        """Выбрать команду по последней позе и опубликовать её (callback таймера)."""
        command = choose_command(self._last_pose, self._linear_speed, self._turn_rate)
        msg = Twist()
        msg.linear.x = command.linear_x
        msg.angular.z = command.angular_z
        self._cmd_pub.publish(msg)

    def _on_set_parameters(self, params: list[Parameter]) -> SetParametersResult:
        """Отклонить недопустимые значения до изменения состояния ноды."""
        for param in params:
            reason = validate_parameter(param.name, param.value)
            if reason is not None:
                self.get_logger().warning(f'отклонено: {reason}')
                return SetParametersResult(successful=False, reason=reason)
        return SetParametersResult(successful=True)

    def _on_parameters_set(self, params: list[Parameter]) -> None:
        """Применить принятые значения; при смене частоты пересоздать таймер."""
        for param in params:
            if param.name == 'linear_speed':
                self._linear_speed = float(param.value)
            elif param.name == 'turn_rate':
                self._turn_rate = float(param.value)
            elif param.name == 'publish_hz':
                period = period_for(float(param.value))
                # Старый таймер уничтожается до создания нового: двух таймеров не бывает.
                self.destroy_timer(self._timer)
                self._timer = self.create_timer(period, self._on_timer)
                self._publish_hz = float(param.value)
                self.get_logger().info(
                    f'publish_hz={self._publish_hz}: таймер пересоздан, период {period:.3f} с')


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
