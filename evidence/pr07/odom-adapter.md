# ПР07. Адаптер одометрии и владельцы tf

## Frames

| | Топик | header.frame_id | child_frame_id | Издатель |
|---|---|---|---|---|
| исходная | `/vehicle/odom_gz` (мост, `/model/course_ackermann/odometry`) | `course_ackermann/odom` | `course_ackermann/base_link` | `/sim/bridge` |
| нормализованная | `/vehicle/odom` | `odom` | `base_link` | `/sim/odom_adapter` |

В копии `src/course_simulation/config/bridge.yaml` изменён только
`ros_topic_name` одометрии: `/vehicle/odom` → `/vehicle/odom_gz`. Нормализация
выполняется один раз — в `odom_adapter` (`course_simulation/odom_adapter.py`):
снимается ровно префикс `course_ackermann/`, а stamp, pose, twist и обе
covariance копируются без изменений. Сообщение с другим префиксом
(`robot2/odom`, `odom`) или с NaN/∞ где-либо в pose/twist/covariance
отклоняется.

## Владельцы преобразований

| Связь | Владелец | Топик |
|---|---|---|
| `odom → base_link` | `odom_adapter` (тот же stamp и поза, что в `/vehicle/odom`) | `/tf` |
| `base_link → camera_link / lidar_link / imu_link` (+ `camera_optical_frame`) | `robot_state_publisher` (URDF/Xacro ПР06) | `/tf_static` |
| `map → odom` | пока никто (AMCL в ПР08) | — |

Мост не публикует tf, второго издателя `odom → base_link` нет.

## Проверка сохранения времени

Тест `test/test_odom_adapter.py::test_frames_normalized_values_preserved`:
stamp (42 с, 125 000 000 нс), позиция, скорость и covariance совпадают у входа
и выхода; `test_transform_has_same_stamp_and_pose` — то же для tf. В живом
опыте (`checks.txt`): `/vehicle/odom_gz` stamp 70 с, `/vehicle/odom` 69 с —
оба из `/clock`; `tf2_echo odom base_link --ros-args -p use_sim_time:=true`
даёт `At time 100.578` и ту же позу, что `/vehicle/odom`.

## Наблюдение: одометрия ≠ реальная поза корпуса

Прогон с поворотом (speed 0.6, steering 0.2 → ω = 0.152 рад/с, радиус ≈ 3,95 м)
упёр робота в северную стену коридора (y = 2). Одометрия контроллера продолжала
интегрировать команду: (3.96, 2.44) → (4.08, 5.21) — это уже за стеной, — а
`gz topic -e -t /world/mcity_minimal/dynamic_pose/info` показывал корпус в
(2.08, 1.16). Одометрия AckermannSteering считается по командам/колёсам и не
доказывает, что корпус действительно переместился. В прямом прогоне для записи
(speed 0.2, 36 с) расхождения нет: `/vehicle/odom` x = 7.333, Gazebo x = 7.390.
