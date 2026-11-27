# ros2

Практические работы курса «Робототехника · ROS 2» (НГУ).

## Среда

ROS 2 запускается в Docker-образе
`tiryoh/ros2-desktop-vnc@sha256:23bbfbd0bac264da8ef39fb599b9d58b209b06603b49e979eba8021286c56b6e`
(ROS 2 Lyrical, рабочий стол по noVNC). Репозиторий монтируется в контейнер,
поэтому evidence сохраняется прямо на хост.

```bash
docker run -d --name ros2 -p 6080:80 --shm-size=512m \
  -v "$PWD":/home/ubuntu/ros2_local \
  tiryoh/ros2-desktop-vnc@sha256:23bbfbd0bac264da8ef39fb599b9d58b209b06603b49e979eba8021286c56b6e
```

Рабочий стол: <http://localhost:6080>. Терминал в контейнере:

```bash
docker exec -it -u ubuntu -w /home/ubuntu/ros2_local ros2 bash
```

Course kit скачивается в `.course-kit/` по инструкции курса и в репозиторий
не коммитится.

## ПР01. Окружение и граф ROS 2

Домены опыта: 26 (рабочий) и 27 (разрыв связи). В каждом терминале:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=26
```

Отчёт среды (терминал C, из корня репозитория):

```bash
mkdir -p evidence/pr01
ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
```

Исправный граф:

```bash
# A — симулятор (в терминале рабочего стола noVNC)
ros2 run turtlesim turtlesim_node
# B — управление стрелками
ros2 run turtlesim turtle_teleop_key
# C — наблюдение
ros2 node list --no-daemon --spin-time 2
ros2 topic list -t
ros2 node info /turtlesim
ros2 topic type /turtle1/pose
POSE_TYPE=$(ros2 topic type /turtle1/pose)
ros2 topic echo /turtle1/pose --once
ros2 topic hz /turtle1/pose   # не меньше 10 с, затем Ctrl+C
```

Разрыв связи: teleop (B) и подписчик (C) перезапускаются в домене 27,
симулятор остаётся в 26:

```bash
export ROS_DOMAIN_ID=27
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-broken.txt 2>&1
printf 'exit=%s\n' "$?"   # ожидается exit=124
```

Восстановление: B и C снова в домене 26:

```bash
export ROS_DOMAIN_ID=26
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-fixed.txt 2>&1
printf 'exit=%s\n' "$?"   # ожидается exit=0
```

Проверка сдачи:

```bash
python3 -m json.tool evidence/pr01/environment.json > /dev/null
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

## ПР02. Пакет turtle_bringup и launch

Корень репозитория — корень colcon-workspace, пакет лежит в
`src/turtle_bringup`. Сборка (в терминале, где подключена только базовая ROS):

```bash
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-select turtle_bringup
```

Запуск (в новом терминале, из корня репозитория):

```bash
source /opt/ros/lyrical/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=26
ros2 launch turtle_bringup sim.launch.py
```

Команда движения (в другом терминале с той же средой):

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Проверка сдачи:

```bash
python3 -m py_compile src/turtle_bringup/launch/sim.launch.py
python3 .course-kit/v1/tools/check_practice.py PR02 --submission .
```

## ПР03. Нода patrol

Пакет `src/patrol`: подписка на `/turtle1/pose`, таймер 0,1 с и издатель
`geometry_msgs/msg/Twist` в **относительный** `cmd_vel`. До первой позы команда
нулевая, затем `linear.x=0.5`, `angular.z=0.3`. Выбор команды — чистая функция
`patrol.command.choose_command`.

Сборка и тесты (из корня репозитория):

```bash
source /opt/ros/lyrical/setup.bash
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
(cd src/patrol && python3 -m pytest test -v)
colcon test --packages-select patrol && colcon test-result --verbose
```

Опыт (A — симулятор, B — patrol, C — наблюдение; везде `ROS_DOMAIN_ID=26`):

```bash
# A
ros2 launch turtle_bringup sim.launch.py
# B — сбой: команда уходит в /cmd_vel, черепаха стоит
ros2 run patrol patrol
# C
ros2 node info /patrol
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic echo /turtle1/pose --once
# B — исправление remap (Ctrl+C, затем)
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
# C — частота команды
timeout --signal=INT 10s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
```

Проверка сдачи:

```bash
python3 .course-kit/v1/tools/check_practice.py PR03 --submission .
```

## ПР04. Параметры patrol

Параметры: `linear_speed` (0.5, допустимо 0…1), `turn_rate` (0.3, −1…1),
`publish_hz` (10.0, 1…30). Недопустимое значение отклоняется до изменения
состояния; допустимая `publish_hz` пересоздаёт таймер.

```bash
# A: ros2 launch turtle_bringup sim.launch.py
# B: ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
# C:
ros2 param get /patrol publish_hz
timeout --signal=INT 10s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
ros2 param set /patrol publish_hz 5.0     # поток 5 Гц
ros2 param set /patrol publish_hz 0.0     # Setting parameter failed, остаётся прежнее
ros2 service call /clear std_srvs/srv/Empty "{}"
ros2 action list -t
```

Тесты и проверка сдачи:

```bash
(cd src/patrol && python3 -m pytest test -v)
colcon test --packages-select patrol && colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR04 --submission .
```

## ПР05. Одна команда запуска, QoS и replay

Пакет `src/course_bringup`, launch `patrol.launch.py`: глобальный turtlesim и
в пространстве имён `patrol`, `pose_relay` (поза → `sensor_pose`, best_effort) и
`pose_subscriber` (QoS из аргумента). Аргументы: `namespace`, `record`,
`bag_dir`, `subscriber_reliability`.

```bash
colcon build --symlink-install && source install/setup.bash
# сбой: reliable-подписчик против best_effort-издателя
ros2 launch course_bringup patrol.launch.py namespace:=robot_a subscriber_reliability:=reliable record:=false
ros2 topic info /robot_a/sensor_pose --verbose
timeout --signal=INT 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once   # exit=124
# исправление
ros2 launch course_bringup patrol.launch.py namespace:=robot_a subscriber_reliability:=best_effort record:=false
timeout --signal=INT 3s ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once
ros2 bag record -s mcap -o evidence/pr05/bag --topics /robot_a/sensor_pose
# повтор той же записи
ros2 bag play evidence/pr05/bag --loop --qos-profile-overrides-path config/qos-overrides.yaml
ros2 bag info evidence/pr05/bag
```

`timeout --signal=INT`: в Lyrical `ros2 topic echo` не завершается по SIGTERM.

```bash
colcon test --packages-select patrol course_bringup && colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR05 --submission .
```

## ПР06. Модель робота и дерево tf

Пакет `src/course_description`: `urdf/vehicle.urdf.xacro` (размеры из
course kit `models/course_ackermann/model.sdf`), `launch/display.launch.py`
(robot_state_publisher + RViz), тесты структуры.

```bash
colcon build --symlink-install --packages-select course_description && source install/setup.bash
xacro src/course_description/urdf/vehicle.urdf.xacro > /tmp/vehicle.urdf
check_urdf /tmp/vehicle.urdf
ros2 launch course_description display.launch.py            # rviz:=false — без окна; zero_joints:=true — колёса в /tf
ros2 run tf2_ros tf2_echo base_link lidar_link               # (0.28, 0, 0.38)
ros2 topic info /tf_static --verbose                         # RELIABLE, TRANSIENT_LOCAL
timeout --signal=INT 4 ros2 topic echo /tf_static --once --qos-durability transient_local --qos-reliability reliable; echo "exit=$?"
timeout --signal=INT 4 ros2 topic echo /tf_static --once --qos-durability volatile --qos-reliability reliable; echo "exit=$?"
colcon test --packages-select course_description && colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR06 --submission .
```

## ПР07. Gazebo и мост ros_gz

Пакет `src/course_simulation`: копии `models/course_ackermann` (камера 20→15 Гц),
`worlds/mcity-minimal.sdf`, `config/bridge.yaml` (одометрия → `/vehicle/odom_gz`,
сенсоры с QoS SENSOR_DATA), launch `simulation.launch.py` (Gazebo headless +
robot_state_publisher + один мост + `drive_adapter` + `odom_adapter`) и
тестовый источник команды `drive_source`.

Контейнеру нужны `apt-get upgrade` и `ros-lyrical-ackermann-msgs`.

```bash
colcon build --symlink-install --packages-up-to course_simulation && source install/setup.bash
export GZ_SIM_RESOURCE_PATH="$PWD/src/course_simulation/models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
ros2 launch course_simulation simulation.launch.py \
  world:=$PWD/src/course_simulation/worlds/mcity-minimal.sdf \
  bridge_config:=$PWD/src/course_simulation/config/bridge.yaml headless:=true
# второй терминал
ros2 run course_simulation drive_source --ros-args -p use_sim_time:=true -p speed:=0.6 -p steering_angle:=0.2
ros2 topic echo /vehicle/gz_cmd_vel --once
timeout 3s gz topic -e -t /model/course_ackermann/cmd_vel -n 1
ros2 run tf2_ros tf2_echo odom base_link --ros-args -p use_sim_time:=true
# запись (вне репозитория — ~350 МиБ)
timeout --preserve-status --signal=INT --kill-after=60s 40s ros2 bag record --storage mcap --use-sim-time \
  -o ~/bags/pr07-sensors --topics /vehicle/camera/image_raw /vehicle/scan /vehicle/imu /vehicle/odom /tf /tf_static /clock
colcon test --packages-select course_simulation && colcon test-result --verbose
python3 .course-kit/v1/tools/check_practice.py PR07 --submission .
```

## ПР08. Локализация AMCL на записи ПР07

Пакет `src/localization_case` (ament_cmake): `launch/localization.launch.py`
(map_server + amcl + lifecycle_manager_localization), `config/amcl.yaml` (копия
профиля kit), `measure_localization.py`, `make_localization_report.py`.
Контейнеру нужны `ros-lyrical-nav2-amcl`, `-nav2-map-server`, `-nav2-lifecycle-manager`.

```bash
colcon build --symlink-install --packages-select localization_case && source install/setup.bash
# A
ros2 launch localization_case localization.launch.py \
  params_file:=$PWD/src/localization_case/config/amcl.yaml map:=$PWD/.course-kit/v1/fixtures/pr08/map.yaml
# B (до player)
ros2 run localization_case measure_localization.py --ros-args -p use_sim_time:=true -p output:=/tmp/metrics.json
# C
ros2 bag play ~/bags/pr07-sensors --topics /vehicle/scan /vehicle/odom /tf /tf_static /clock
ros2 run tf2_ros tf2_echo map odom --ros-args -p use_sim_time:=true
python3 .course-kit/v1/tools/validate_localization.py evidence/pr08/localization.json \
  --schema .course-kit/v1/fixtures/pr08/localization-result-v1.schema.json \
  --map-yaml evidence/pr08/map.yaml --map-pgm evidence/pr08/map.pgm
python3 .course-kit/v1/tools/check_practice.py PR08 --submission .
```
