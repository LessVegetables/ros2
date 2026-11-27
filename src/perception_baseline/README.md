# perception_baseline (ПР09)

Тонкая ROS-обёртка над тем же baseline, что в `.course-kit/v1/tools/evaluate_perception.py`
(красные связные области, `baseline-detector.json`, `calibration.json` — копии из
course kit v1-w12 в `config/`).

| Топик | Тип |
|-------|-----|
| вход `/camera/image_raw` | `sensor_msgs/msg/Image`, rgb8, 8×6, sensor-data QoS |
| вход `/camera/depth/image_raw` | `sensor_msgs/msg/Image`, 16UC1, мм, тот же stamp и `camera_optical_frame` |
| `/perception/detections_2d` | `vision_msgs/msg/Detection2DArray` |
| `/perception/objects_3d` | `vision_msgs/msg/Detection3DArray` — только детекции с пространственной привязкой |
| `/perception/status` | `diagnostic_msgs/msg/DiagnosticArray`, `reason`: missing_depth, zero_depth, stamp_mismatch, frame_mismatch, invalid_depth |

Запуск и показ (из корня репозитория, после `colcon build` и `source install/setup.bash`):

```bash
ros2 run perception_baseline perception_baseline
# во втором терминале
ros2 topic echo /perception/status
# в третьем — пара из fixture (mode: ok | zero_depth | no_depth | stamp_mismatch | frame_mismatch)
ros2 run perception_baseline publish_pair --ros-args \
  -p fixture:=$PWD/.course-kit/v1/fixtures/pr09 -p sample:=sample-01 -p mode:=ok
```

Для `sample-01` (bbox [2, 2, 2, 2]) центр u=3, v=3, Z=1 м:
X=(3−3,5)·1/8=−0,0625 м, Y=(3−2,5)·1/8=0,0625 м. Точка — поверхность на луче
центрального пикселя, `bbox.size` нулевой: размер и ориентация не оцениваются.

Тесты: `colcon test --packages-select perception_baseline && colcon test-result --verbose`.
