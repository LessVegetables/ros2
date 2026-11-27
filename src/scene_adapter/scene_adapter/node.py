"""Нода scene_adapter: mock / cache / live → /perception/scene (SceneDescription v1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import rclpy
from rclpy.clock import Clock, ClockType
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from robotics_course_interfaces.msg import SceneDescription

from scene_adapter.convert import ConversionError, to_msg
from scene_adapter.core import (
    Backend, canonical_unknown, evaluate_scene, load_schema, REASON_INVALID_SCHEMA,
    SceneCache, sha256_file,
)

MODES = ('mock', 'cache', 'live')


class SceneAdapter(Node):
    """Читает ответ VLM из выбранного источника, проверяет и публикует наблюдение."""

    def __init__(self, backend: Optional[Backend] = None) -> None:
        super().__init__('scene_adapter')
        self.declare_parameter('mode', 'mock')
        self.declare_parameter('fixture_path', '')
        self.declare_parameter('schema_path', '')
        self.declare_parameter('image_path', '')
        self.declare_parameter('cache_dir', '')
        self.declare_parameter('prompt_path', '')
        self.declare_parameter('model_id', '')
        self.declare_parameter('generation_config', '{}')
        self.declare_parameter('abstain_threshold', 0.5)
        self.declare_parameter('max_age_s', 0.25)
        self.declare_parameter('publish_period_s', 1.0)

        self.mode = self.get_parameter('mode').value
        if self.mode not in MODES:
            raise ValueError(f'mode должен быть одним из {MODES}, получено {self.mode!r}')
        if self.mode == 'live' and backend is None:
            raise RuntimeError(
                'mode=live требует явно внедрённого backend; скрытый сетевой вызов запрещён')
        self.schema = load_schema(Path(self.get_parameter('schema_path').value))
        self.cache: Optional[SceneCache] = None
        if self.mode in ('cache', 'live'):
            self.cache = SceneCache(Path(self.get_parameter('cache_dir').value), backend)

        self.pub = self.create_publisher(SceneDescription, '/perception/scene', 10)
        # Таймер по steady-часам: замороженный /clock не должен останавливать публикацию,
        # а возраст наблюдения считается по ROS-часам ноды (use_sim_time поддерживается).
        self.timer = self.create_timer(
            float(self.get_parameter('publish_period_s').value), self.tick,
            clock=Clock(clock_type=ClockType.STEADY_TIME))

    def read_raw(self) -> tuple[Any, str]:
        """Сырой ответ и значение source для выбранного режима."""
        if self.mode == 'mock':
            path = Path(self.get_parameter('fixture_path').value)
            return json.loads(path.read_text(encoding='utf-8')), 'mock'
        assert self.cache is not None
        raw, hit = self.cache.get(
            sha256_file(Path(self.get_parameter('image_path').value)),
            Path(self.get_parameter('prompt_path').value),
            str(self.get_parameter('model_id').value),
            json.loads(self.get_parameter('generation_config').value))
        return raw, ('cache' if hit else 'live')

    def tick(self) -> None:
        """Один цикл: прочитать, проверить, преобразовать и опубликовать."""
        try:
            raw, source = self.read_raw()
        except RuntimeError as error:
            self.get_logger().error(str(error))
            return
        now_s = self.get_clock().now().nanoseconds * 1e-9
        scene = evaluate_scene(
            raw, self.schema, now_s=now_s, source=source,
            abstain_threshold=float(self.get_parameter('abstain_threshold').value),
            max_age_s=float(self.get_parameter('max_age_s').value))
        try:
            msg = to_msg(scene)
        except ConversionError:
            msg = to_msg(canonical_unknown(raw, REASON_INVALID_SCHEMA, source))
        self.pub.publish(msg)
        self.get_logger().info(
            f'scene: {scene["status"]} {scene["status_reason"]!r} source={source} '
            f'now_s={now_s:.3f} stamp_s={scene["stamp_s"]}')


def main(args: Optional[list[str]] = None) -> None:
    """Точка входа ros2 run scene_adapter scene_adapter."""
    rclpy.init(args=args)
    node = SceneAdapter()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
