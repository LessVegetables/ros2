# ПР06. Системы координат Ackermann-робота

Модель: `src/course_description/urdf/vehicle.urdf.xacro`. Размеры взяты из
course kit `models/course_ackermann/model.sdf` (v1-w12): база 0,80 м, колея 0,62 м,
радиус колеса 0,12 м, ширина 0,07 м, корпус 1,05 × 0,52 × 0,22 м (центр на 0,12 м
над `base_link`), масса корпуса 12 кг. Всё в СИ, оси REP-103 (x вперёд, y влево,
z вверх). Параметры заданы `xacro:property`, тензоры инерции — макросами
`box_inertia` / `wheel_inertia` по формулам однородных тел.

Запуск: `ros2 launch course_description display.launch.py` (robot_state_publisher
по развёрнутому Xacro + RViz, Fixed Frame = `base_link`).

| Родитель → дочернее | Joint (тип) | Ожидаемое преобразование (xyz, м; rpy, рад) | Кто публикует | Топик |
|---------------------|-------------|---------------------------------------------|---------------|-------|
| `base_link` → `camera_link` | `camera_joint` (fixed) | (0.28, 0, 0.38); (0, 0, 0) | robot_state_publisher | `/tf_static` |
| `camera_link` → `camera_optical_frame` | `camera_optical_joint` (fixed) | (0, 0, 0); (−π/2, 0, −π/2): z вперёд, x вправо, y вниз | robot_state_publisher | `/tf_static` |
| `base_link` → `lidar_link` | `lidar_joint` (fixed) | (0.28, 0, 0.38); (0, 0, 0) | robot_state_publisher | `/tf_static` |
| `base_link` → `imu_link` | `imu_joint` (fixed) | (0.28, 0, 0.38); (0, 0, 0) | robot_state_publisher | `/tf_static` |
| `base_link` → `front_left_knuckle` | `front_left_steering_joint` (revolute z, ±0.55) | (0.40, 0.31, 0); поворот руля из joint_states | robot_state_publisher по `/joint_states` | `/tf` |
| `base_link` → `front_right_knuckle` | `front_right_steering_joint` (revolute z, ±0.55) | (0.40, −0.31, 0) | robot_state_publisher по `/joint_states` | `/tf` |
| `front_left_knuckle` → `front_left_wheel` | `front_left_wheel_joint` (continuous y) | (0, 0, 0); вращение колеса | robot_state_publisher по `/joint_states` | `/tf` |
| `front_right_knuckle` → `front_right_wheel` | `front_right_wheel_joint` (continuous y) | (0, 0, 0) | robot_state_publisher по `/joint_states` | `/tf` |
| `base_link` → `rear_left_wheel` | `rear_left_wheel_joint` (continuous y) | (−0.40, 0.31, 0) | robot_state_publisher по `/joint_states` | `/tf` |
| `base_link` → `rear_right_wheel` | `rear_right_wheel_joint` (continuous y) | (−0.40, −0.31, 0) | robot_state_publisher по `/joint_states` | `/tf` |

Каждое преобразование публикует ровно один участник — robot_state_publisher.
Подвижные связи (кулаки и колёса) появляются в `/tf` только при наличии
`/joint_states`; для зачёта они не нужны (`display.launch.py zero_joints:=true`
публикует нулевые положения, чтобы увидеть колёса в RViz). `map → odom` и
`odom → base_link` в этой работе никто не публикует: их владельцами станут
локализация и адаптер одометрии (ПР07–ПР08), поэтому Fixed Frame = `map`/`odom`
в RViz ожидаемо даёт ошибку.

## Проверка (выводы — `model-check.txt`, `tf-qos.txt`)

- `check_urdf`: root `base_link`, 7 дочерних звеньев, дерево связно.
- `tf2_echo base_link lidar_link` → Translation [0.280, 0.000, 0.380], RPY 0.
  Так же для `camera_link` и `imu_link`; `camera_optical_frame` → RPY (−90°, 0, −90°).
- `view_frames`: рёбра `base_link→camera_link`, `camera_link→camera_optical_frame`,
  `base_link→imu_link`, `base_link→lidar_link` (без joint_states — только статика).
  PDF графа: `lab6/frames.pdf`, скриншоты RViz: `lab6/`.

## Дефект: неверный parent лидара

Отдельное изменение (`defect.patch`): макрос сенсора получил параметр `parent`, а
лидар подвешен к `camera_link` с тем же offset (0.28, 0, 0.38). Вывод — `defect.txt`.

| Проверка | Дефект | Исправлено |
|----------|--------|------------|
| `check_urdf` | **проходит**: дерево связно, root `base_link`, у `camera_link` 2 ребёнка | проходит |
| `tf2_echo base_link lidar_link` | (0.560, 0, 0.760) — лидар висит над передком в 0,76 м | (0.280, 0, 0.380) |
| `view_frames` | ребро `camera_link → lidar_link` | `base_link → lidar_link` |
| `test_description.py` | 2 failed: `assert 'camera_link' == 'base_link'` | 9 passed |
| RViz | оранжевый цилиндр лидара отделён от корпуса (`lab6/pr06-defect-rviz.jpg`) | на корпусе (`lab6/pr06-fixed-rviz.jpg`) |

Offset в URDF задаётся относительно **родителя**, поэтому смена parent сложила два
смещения (камера + лидар). Структурная проверка этого не видит: дерево остаётся
связным и ацикличным. Смысл связи проверяет только тест ожидаемого parent и
положения.
