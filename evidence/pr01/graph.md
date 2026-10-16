# ПР01. Граф ROS 2 и разрыв связи доменами

Среда: Docker `tiryoh/ros2-desktop-vnc` (Ubuntu 26.04.1, ROS 2 Lyrical,
`rmw_fastrtps_cpp`), подробности в `environment.json`. Три терминала в одном
контейнере: A — `turtlesim_node` (окно в рабочем столе noVNC), B — `turtle_teleop_key`,
C — наблюдение. Рабочий домен — 26, домен для разрыва — 27.

Во всех терминалах перед опытом:

```bash
source /opt/ros/lyrical/setup.bash
export ROS_DOMAIN_ID=26
```

## 1. Исправный граф (все участники в домене 26)

A: `ros2 run turtlesim turtlesim_node`, B: `ros2 run turtlesim turtle_teleop_key`.
Стрелки в B двигают черепаху, в окне TurtleSim остаётся след траектории.

### Ноды

```text
$ ros2 node list --no-daemon --spin-time 2
/teleop_turtle
/turtlesim
```

| Нода | Роль |
|------|------|
| `/turtlesim` | симулятор: подписан на команды скорости, публикует позу и цвет под черепахой, предоставляет сервисы и action управления |
| `/teleop_turtle` | телеуправление: читает стрелки с клавиатуры и публикует `geometry_msgs/msg/Twist` в `/turtle1/cmd_vel` (клавиши `g b v c d e r t` вызывают action `/turtle1/rotate_absolute`) |

### Топики и типы

```text
$ ros2 topic list -t
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim_msgs/msg/Color]
/turtle1/pose [turtlesim_msgs/msg/Pose]
```

| Топик | Тип | Издатель → подписчик |
|-------|-----|----------------------|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | `/teleop_turtle` → `/turtlesim` |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | `/turtlesim` → наблюдатели (CLI) |
| `/turtle1/color_sensor` | `turtlesim_msgs/msg/Color` | `/turtlesim` → наблюдатели |
| `/rosout` | `rcl_interfaces/msg/Log` | все ноды → журнал |
| `/parameter_events` | `rcl_interfaces/msg/ParameterEvent` | служебный топик параметров |

В Lyrical тип позы — `turtlesim_msgs/msg/Pose` (в Jazzy был `turtlesim/msg/Pose`).

### Интерфейсы ноды `/turtlesim`

```text
$ ros2 node info /turtlesim
/turtlesim
  Subscribers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /turtle1/cmd_vel: geometry_msgs/msg/Twist
  Publishers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
    /turtle1/color_sensor: turtlesim_msgs/msg/Color
    /turtle1/pose: turtlesim_msgs/msg/Pose
  Service Servers:
    /clear: std_srvs/srv/Empty
    /kill: turtlesim_msgs/srv/Kill
    /reset: std_srvs/srv/Empty
    /spawn: turtlesim_msgs/srv/Spawn
    /turtle1/set_pen: turtlesim_msgs/srv/SetPen
    /turtle1/teleport_absolute: turtlesim_msgs/srv/TeleportAbsolute
    /turtle1/teleport_relative: turtlesim_msgs/srv/TeleportRelative
    /turtlesim/describe_parameters: rcl_interfaces/srv/DescribeParameters
    /turtlesim/get_parameter_types: rcl_interfaces/srv/GetParameterTypes
    /turtlesim/get_parameters: rcl_interfaces/srv/GetParameters
    /turtlesim/get_type_description: type_description_interfaces/srv/GetTypeDescription
    /turtlesim/list_parameters: rcl_interfaces/srv/ListParameters
    /turtlesim/set_parameters: rcl_interfaces/srv/SetParameters
    /turtlesim/set_parameters_atomically: rcl_interfaces/srv/SetParametersAtomically
  Service Clients:

  Action Servers:
    /turtle1/rotate_absolute: turtlesim_msgs/action/RotateAbsolute
  Action Clients:

```

### Поза

```text
$ ros2 topic type /turtle1/pose
turtlesim_msgs/msg/Pose
$ POSE_TYPE=$(ros2 topic type /turtle1/pose); echo "$POSE_TYPE"
turtlesim_msgs/msg/Pose
$ ros2 topic echo /turtle1/pose --once
x: 4.805058002471924
y: 4.542709827423096
theta: -0.9391853213310242
linear_velocity: 0.0
angular_velocity: 0.0
---
```

Черепаха в этот момент стояла (скорости 0), но поза всё равно публикуется.

### Частота `/turtle1/pose`

```text
$ time ros2 topic hz /turtle1/pose
average rate: 62.427
        min: 0.013s max: 0.021s std dev: 0.00176s window: 62
average rate: 62.445
        min: 0.012s max: 0.021s std dev: 0.00170s window: 125
average rate: 62.508
        min: 0.012s max: 0.021s std dev: 0.00162s window: 187
average rate: 62.461
        min: 0.012s max: 0.021s std dev: 0.00162s window: 250
average rate: 62.469
        min: 0.012s max: 0.021s std dev: 0.00168s window: 312
average rate: 62.504
        min: 0.011s max: 0.021s std dev: 0.00175s window: 375
average rate: 62.500
        min: 0.011s max: 0.021s std dev: 0.00175s window: 438
^C
real    0m9.106s
```

Итог: **≈ 62,5 Гц** (последнее окно — 438 сообщений, период 11–21 мс,
σ ≈ 1,7 мс). Команда работала 9,1 с по `time` вместе с запуском CLI. Результат
совпадает с ожидаемыми 62,5 Гц от таймера turtlesim с периодом 16 мс:
нагрузка VNC/Docker на частоту не повлияла.

## 2. Сбой: teleop и подписчик в домене 27

Симулятор A остаётся в домене 26. В B teleop остановлен через Ctrl+C и
перезапущен:

```bash
export ROS_DOMAIN_ID=27
ros2 run turtlesim turtle_teleop_key
```

Стрелки больше не двигают черепаху. В C:

```text
$ export ROS_DOMAIN_ID=27; ros2 node list --no-daemon --spin-time 2
/teleop_turtle
$ timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-broken.txt 2>&1; printf 'exit=%s\n' "$?"
exit=124
```

В домене 27 видна только `/teleop_turtle`, а `/turtlesim` нет. Поза за 5 с
не пришла: `exit=124` — это код `timeout` при истечении времени, а
`pose-broken.txt` пустой (0 байт): нет ни сообщений, ни ошибок импорта
или типа. Тип пришлось передать явно (`"$POSE_TYPE"`), потому что в домене 27
нет издателя, у которого CLI мог бы его узнать. Тест повторялся дважды, оба
раза `exit=124`.

## 3. Восстановление: teleop и подписчик снова в домене 26

В B teleop остановлен и запущен заново с `ROS_DOMAIN_ID=26`. В C изменены
только домен и имя файла:

```text
$ export ROS_DOMAIN_ID=26; ros2 node list --no-daemon --spin-time 2
/teleop_turtle
/turtlesim
$ timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once > evidence/pr01/pose-fixed.txt 2>&1; printf 'exit=%s\n' "$?"
exit=0
```

`pose-fixed.txt`:

```text
x: 4.805058002471924
y: 4.542709827423096
theta: -0.9391853213310242
linear_velocity: 0.0
angular_velocity: 0.0
---
```

Обе ноды снова видны, поза пришла (та же точка: черепаха не двигалась),
стрелки снова управляют черепахой.

## Сравнение «до / сбой / после»

| Стадия | Домен A (`turtlesim`) | Домен B (`teleop`) | Домен C (CLI) | `node list` в C | Поза в C | exit | Управление |
|--------|----|----|----|-----------------|----------|------|------------|
| до | 26 | 26 | 26 | `/teleop_turtle`, `/turtlesim` | есть, ≈ 62,5 Гц | — | работает |
| сбой | 26 | 27 | 27 | только `/teleop_turtle` | нет за 5 с | 124 | не работает |
| после | 26 | 26 | 26 | `/teleop_turtle`, `/turtlesim` | есть | 0 | работает |

## Причина

`ROS_DOMAIN_ID` задаёт DDS-домен, в котором нода ищет других участников
(от домена зависят порты discovery). Участники из разных доменов не
обнаруживают друг друга, поэтому команды `/turtle1/cmd_vel` из домена 27 не
доходят до симулятора в домене 26, а подписчик из домена 27 не видит
издателя `/turtle1/pose`. Установка ROS и сами программы исправны: в сбое
изменилась только конфигурация части участников.

Значение домена читается один раз, при запуске ноды. `export` меняет
переменную только в оболочке и для процессов, запущенных после него, а уже
работающая нода остаётся в старом домене. Поэтому teleop пришлось
перезапускать после каждого `export`. Каждая CLI-команда в C — новый процесс,
и она сразу берёт новый домен. Симулятор всё время работал в исходном
домене 26, поэтому его, как и установку ROS, трогать не понадобилось.
Достаточно было вернуть в домен 26 тех участников, которые из него ушли.
