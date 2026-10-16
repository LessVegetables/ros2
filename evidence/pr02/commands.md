# ПР02. Терминал, пакет и запуск turtlesim

Среда та же, что в ПР01: Docker `tiryoh/ros2-desktop-vnc` (Ubuntu 26.04.1,
ROS 2 Lyrical), домен 26. Корень репозитория `/home/ubuntu/ros2_local` —
это и корень colcon-workspace. Терминалы: A — launch (рабочий стол noVNC),
B — издатель команд, C — сборка и наблюдение.

## 1. Три команды Linux

### `ls -a`

```text
$ cd "$(git rev-parse --show-toplevel)"; pwd; ls -a
/home/ubuntu/ros2_local
.          .course-kit  AI_USAGE.md  robotics-course-kit-v1-w06-6eda53e1c566.tar.gz
..         .git         README.md    robotics-course-kit-v1-w06-6eda53e1c566.tar.gz.sha256.txt
.DS_Store  .github      evidence
.claude    .gitignore   lab1
```

Показывает содержимое каталога вместе со скрытыми файлами (имена с точки).
Без `-a` не видно `.git`, `.github` с CI, `.gitignore` и `.course-kit`.
Сначала `git rev-parse --show-toplevel` нашёл корень репозитория, `cd` перешёл в
него, а `pwd` подтвердил путь. Этот путь не совпадает с `ros2 pkg prefix turtlesim`
(`/opt/ros/lyrical`): там установлен системный пакет, а здесь мой workspace.

### `mkdir -p`

```text
$ mkdir -p src evidence/pr02; printenv ROS_DISTRO ROS_DOMAIN_ID; ros2 pkg prefix turtlesim
lyrical
26
/opt/ros/lyrical
```

`mkdir -p` создаёт каталоги вместе с недостающими родителями (`evidence/pr02`)
и не выдаёт ошибку, если каталог уже есть, поэтому команду можно безопасно
повторять. `printenv` подтвердил, что в терминале подключён Lyrical и домен 26.

### `colcon build ... 2>&1 | tee` с `set -o pipefail`

```text
$ set -o pipefail; colcon build --symlink-install --packages-select turtle_bringup 2>&1 | tee evidence/pr02/build-empty.txt; echo "build exit=$?"
Starting >>> turtle_bringup
Finished <<< turtle_bringup [1.14s]

Summary: 1 package finished [1.32s]
build exit=0
```

`2>&1` направляет stderr туда же, куда stdout. `|` передаёт этот общий поток
программе `tee`, а `tee` одновременно показывает его в терминале и пишет в
файл. Без `pipefail` статусом конвейера был бы статус последней команды
(`tee`, почти всегда 0). С `pipefail` ошибка `colcon` даёт ненулевой `exit`.
Здесь `exit=0`, пакет собран.

### `>` и `|`

`>` перенаправляет вывод команды **в файл** и заменяет его прежнее
содержимое. Так в ПР01 `ros2 doctor --report > doctor.txt` писал отчёт
в файл, ничего не показывая на экране. `|` передаёт вывод **на вход другой
программе**, и файл при этом не создаётся. Поэтому для «показать и сохранить»
используется `| tee файл`.

### `source` и запуск новой программы

`source /opt/ros/lyrical/setup.bash` выполняет скрипт **в текущей оболочке**.
Переменные, которые он задаёт (`ROS_DISTRO`, `AMENT_PREFIX_PATH`, `PATH`,
`PYTHONPATH`), остаются в этом терминале и наследуются всеми командами,
запущенными из него. Если запустить скрипт как программу (`bash setup.bash`),
он выполнится в дочернем процессе, и после его завершения изменения окружения
пропадут. `source install/setup.bash` добавил к базовой ROS мой workspace, и
только после этого `ros2 pkg prefix turtle_bringup` нашёл пакет. Ни сборка, ни
`source` не запускают нод.

## 2. Пустой пакет

```text
$ cd src && ros2 pkg create --build-type ament_python --license Apache-2.0 turtle_bringup --dependencies launch launch_ros turtlesim; cd ..
...
$ ls src/turtle_bringup
LICENSE  package.xml  resource  setup.cfg  setup.py  test  turtle_bringup
```

Сборка пустого пакета прошла успешно (`build-empty.txt`, `exit=0`). В новом
терминале:

```text
$ source /opt/ros/lyrical/setup.bash && source install/setup.bash && ros2 pkg prefix turtle_bringup
/home/ubuntu/ros2_local/install/turtle_bringup
```

Пакет найден в `install` моего workspace, но нода от этого не появилась.

## 3. Launch-файл: запуск, граф, остановка

В `package.xml` и `setup.py` обновлены описание и сопровождающий, добавлен
`launch/sim.launch.py` и запись `('share/turtle_bringup/launch', glob('launch/*.launch.py'))`
в `data_files`. Итоговая сборка: `build.txt`, `exit=0`.

A — проверка установленного ресурса и запуск:

```text
$ ros2 pkg prefix turtle_bringup; ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
/home/ubuntu/ros2_local/install/turtle_bringup
sim.launch.py
$ ros2 launch turtle_bringup sim.launch.py
[INFO] [launch]: All log files can be found below /home/ubuntu/.ros/log/2026-10-16-08-02-32-460493-bcf8c512d8e2-2703
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [turtlesim_node-1]: process started with pid [2712]
[turtlesim_node-1] [INFO] [1792137752.663022753] [turtlesim]: Starting turtlesim with node name /turtlesim
[turtlesim_node-1] [INFO] [1792137752.667396253] [turtlesim]: Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000]
```

Открылось одно окно TurtleSim. C:

```text
$ ros2 node list --no-daemon --spin-time 2
/turtlesim
```

Остановка: Ctrl+C в A.

```text
^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)
[turtlesim_node-1] [INFO] [1792137802.702045971] [rclcpp]: signal_handler(signum=2)
[INFO] [turtlesim_node-1]: process has finished cleanly [pid 2712]
```

Окно закрылось. В C нода пропала, вывод пустой:

```text
$ ros2 node list --no-daemon --spin-time 2
$
```

launch передал SIGINT дочернему процессу, и тот завершился сам (`finished
cleanly`). Повторный `ros2 launch turtle_bringup sim.launch.py` (pid 2843)
снова создал `/turtlesim` в той же стартовой точке. Он работал до конца опыта.

## 4. Одна команда — одно движение

C — тип и начальная поза:

```text
$ ros2 topic type /turtle1/pose; ros2 topic echo /turtle1/pose --once
turtlesim_msgs/msg/Pose
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
---
```

B:

```text
$ ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))
```

Ожидание: `linear.x = 1` — вперёд по курсу (θ = 0, то есть вправо по оси x),
`angular.z = 0.5` — поворот против часовой стрелки. turtlesim выполняет
команду около 1 с и останавливается. Значит, черепаха проедет дугу радиусом
v/ω = 2 и повернётся на 0,5 рад: Δx = 2·sin 0,5 ≈ 0,96, Δy = 2·(1 − cos 0,5) ≈ 0,24.

C — поза после остановки:

```text
$ ros2 topic echo /turtle1/pose --once
x: 6.509308815002441
y: 5.796990871429443
theta: 0.5040000081062317
linear_velocity: 0.0
angular_velocity: 0.0
---
```

Факт: Δx = 0,965, Δy = 0,253, Δθ = 0,504 рад. Это совпадает с расчётом:
черепаха немного проехала вправо-вверх по дуге и встала. Одна публикация
даёт одно короткое движение, а не бесконечное.

## 5. Сбой имени и исправление

### Сбой: тот же Twist в `/cmd_vel`

B:

```text
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))
...
publishing #38: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))
^C
```

Издатель отправил 38 сообщений. Черепаха всё это время стояла. C, пока
издатель работал:

```text
$ ros2 topic info /cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: _ros2cli_2972
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: PUBLISHER
GID: 01.0f.eb.7d.9c.0b.65.93.00.00.00.00.00.00.07.03
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (10)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 0

$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 0

Subscription count: 1

Node name: turtlesim
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: SUBSCRIPTION
GID: 01.0f.eb.7d.1b.0b.63.ac.00.00.00.00.00.00.1c.04
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (7)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

$ ros2 topic echo /turtle1/pose --once
x: 6.509308815002441
y: 5.796990871429443
theta: 0.5040000081062317
linear_velocity: 0.0
angular_velocity: 0.0
---
```

Поза не изменилась с конца шага 4, скорости нулевые.

### Исправление: изменено только имя на `/turtle1/cmd_vel`

B (тип, значения, частота и домен те же):

```text
$ ros2 topic pub --rate 1 --wait-matching-subscriptions 0 /turtle1/cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}'
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))
...
publishing #23: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))
^C
```

Черепаха поехала по окружности радиусом 2 (v/ω = 1/0,5) и нарисовала её
пером. C, пока издатель работал:

```text
$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: _ros2cli_3038
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: PUBLISHER
GID: 01.0f.eb.7d.de.0b.1f.58.00.00.00.00.00.00.07.03
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (10)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 1

Node name: turtlesim
Node namespace: /
Topic type: geometry_msgs/msg/Twist
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a
Endpoint type: SUBSCRIPTION
GID: 01.0f.eb.7d.1b.0b.63.ac.00.00.00.00.00.00.1c.04
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (7)
  Durability: VOLATILE
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

$ ros2 topic echo /turtle1/pose --once
x: 7.431099891662598
y: 8.184983253479004
theta: 1.8928147554397583
linear_velocity: 1.0
angular_velocity: 0.5
---
```

После Ctrl+C в B черепаха остановилась:

```text
$ ros2 topic echo /turtle1/pose --once
x: 4.351099967956543
y: 5.933539867401123
theta: -0.6383705735206604
linear_velocity: 0.0
angular_velocity: 0.0
---
```

### Сравнение «до / сбой / после»

| Стадия | Топик издателя | Издатели / подписчики на нём | Подписчики на `/turtle1/cmd_vel` | Поза | Движение |
|--------|----------------|------------------------------|----------------------------------|------|----------|
| до (`--once`) | `/turtle1/cmd_vel` | — | 1 (`turtlesim`) | (5,54; 5,54; 0) → (6,51; 5,80; 0,50) | короткая дуга |
| сбой | `/cmd_vel` | 1 (`_ros2cli_2972`) / **0** | 1 (`turtlesim`), издателей 0 | (6,51; 5,80; 0,50), скорости 0 | нет |
| после | `/turtle1/cmd_vel` | 1 (`_ros2cli_3038`) / **1** (`turtlesim`) | 1 | v = 1,0, ω = 0,5 во время движения | окружность |

### Почему правильного типа недостаточно

В сбое тип совпадал полностью: `geometry_msgs/msg/Twist` и даже одинаковый
`Topic type hash` на `/cmd_vel` и `/turtle1/cmd_vel`. Домен и QoS тоже были
те же. Но издатель и подписчик сопоставляются **по полному имени топика**.
`/cmd_vel` и `/turtle1/cmd_vel` — два разных топика. Тип только определяет,
могут ли совпавшие по имени конечные точки обмениваться данными.

**Обнаружение и доставка — разные вещи.** Обнаружение сработало: издатель
`_ros2cli_2972` виден в графе (`Publisher count: 1`), его видит CLI, и он
находится в том же домене, что и turtlesim. Доставки не было, потому что у
этого издателя нет ни одного подписчика (`Subscription count: 0`). Сообщения
уходили в топик, который никто не слушал, а `--wait-matching-subscriptions 0`
позволил публиковать без ожидания и без ошибки. После исправления имени у
нового издателя `_ros2cli_3038` появился подписчик `turtlesim` (1 / 1), и
та же команда дала движение.

Это различие между тремя уровнями: файл `sim.launch.py` на диске (в `src` и
установленный в `install/.../share`) сам ничего не делает; запущенная нода
`/turtlesim` — участник графа; сообщение доходит, только если имя, тип и
домен издателя совпадают с подписчиком.
