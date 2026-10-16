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
