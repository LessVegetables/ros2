# ПР03. Первая нода: поза и команда

Среда: Docker `tiryoh/ros2-desktop-vnc` (Ubuntu 26.04, ROS 2 Lyrical,
`rmw_fastrtps_cpp`), домен 26, корень репозитория `/home/ubuntu/ros2_local` —
корень colcon-workspace. Тип позы из `ros2 topic type /turtle1/pose` —
`turtlesim_msgs/msg/Pose`, поэтому в `package.xml` зависимость `turtlesim_msgs`.

Пакет `src/patrol` (ament_python): исполняемая команда `patrol`
(`patrol.patrol:main`), чистая логика в `patrol/command.py`, тесты в
`src/patrol/test/test_command.py`.

## Устройство ноды

| Часть | Где | Что делает |
|-------|-----|------------|
| подписка | `self._pose_sub` на `/turtle1/pose` | callback `_on_pose` только сохраняет последнее сообщение в `self._last_pose` |
| таймер | `self._timer`, период 0,1 с | callback `_on_timer` берёт команду из `choose_command(self._last_pose)` и публикует её |
| издатель | `self._cmd_pub`, тип `Twist`, имя **относительное** `cmd_vel` | без remap разрешается в `/cmd_vel` |
| чистая функция | `choose_command(pose)` | `None` → `(0, 0)`; поза есть → `(0.5, 0.3)`, значения ограничены ±1 |

### Роли init, spin, callback и Ctrl+C

- `rclpy.init()` поднимает контекст ROS: разбирает `--ros-args` (в том числе
  `-r cmd_vel:=...`), создаёт middleware-участника. До него нельзя создать ноду.
  Конструктор `Patrol()` лишь **регистрирует** подписку, издатель и таймер —
  сам по себе он ничего не публикует.
- `rclpy.spin(node)` — цикл исполнителя: ждёт событий (пришло сообщение, истёк
  таймер) и вызывает соответствующие callbacks в этом же потоке. Без spin
  callbacks никогда не выполнятся.
- Callback — короткая функция, которую вызывает исполнитель. Подписка только
  сохраняет позу; всю работу делает callback таймера, раз в 0,1 с. Ничего
  долгого в callbacks нет, иначе spin не успеет обслужить остальные события.
- Ctrl+C посылает SIGINT. rclpy превращает его в `KeyboardInterrupt` (или
  `ExternalShutdownException`), spin завершается, `finally` уничтожает ноду и
  вызывает `rclpy.try_shutdown()`. **Отдельная нулевая команда при выходе не
  публикуется**: черепаха останавливается сама, потому что turtlesim выполняет
  последний Twist около 1 с и без новых команд встаёт. Исчезновение процесса —
  не мгновенная команда торможения.

## Сбой: patrol без remap

A: `ros2 launch turtle_bringup sim.launch.py`, B: `ros2 run patrol patrol`.

```text
$ ros2 node list --no-daemon --spin-time 2
/patrol
/turtlesim

$ ros2 node info /patrol
/patrol
  Subscribers:
    /turtle1/pose: turtlesim_msgs/msg/Pose
  Publishers:
    /cmd_vel: geometry_msgs/msg/Twist
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
  ...

$ ros2 topic info /cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: patrol
Node namespace: /
Endpoint type: PUBLISHER
QoS profile:
  Reliability: RELIABLE
  History (Depth): KEEP_LAST (10)
  Durability: VOLATILE

Subscription count: 0

$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 0

Subscription count: 1

Node name: turtlesim
Node namespace: /
Endpoint type: SUBSCRIPTION

$ ros2 topic echo /turtle1/pose --once      # и повторно через 2 с — то же самое
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
```

Лог patrol: `команда в /cmd_vel каждые 0.1 с`. Нода получает позу (подписка
`/turtle1/pose` есть), команды публикуются, но в `/cmd_vel` нет подписчиков, а
turtlesim слушает `/turtle1/cmd_vel`. Черепаха стоит в стартовой точке.

**Причина.** Имя `cmd_vel` в коде относительное и разрешается от пространства
имён ноды (`/`) в `/cmd_vel`. Издатель и подписчик сопоставляются по полному
имени топика; тип `Twist` у обоих совпадает, но это разные топики.

## Исправление: remap при запуске

B: Ctrl+C, затем `ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel`.
Код не менялся: remap переименовывает топик издателя при запуске.

```text
$ ros2 node info /patrol
/patrol
  Subscribers:
    /turtle1/pose: turtlesim_msgs/msg/Pose
  Publishers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
    /turtle1/cmd_vel: geometry_msgs/msg/Twist

$ ros2 topic info /turtle1/cmd_vel --verbose
Type: geometry_msgs/msg/Twist

Publisher count: 1

Node name: patrol
Endpoint type: PUBLISHER

Subscription count: 1

Node name: turtlesim
Endpoint type: SUBSCRIPTION

$ ros2 topic echo /turtle1/pose --once
x: 7.1980390548706055
y: 7.0374298095703125
theta: 1.4639999866485596
linear_velocity: 0.5
angular_velocity: 0.30000001192092896

$ ros2 topic echo /turtle1/pose --once      # через 2 с
x: 6.651389122009277
y: 8.453518867492676
theta: 2.409600019454956
linear_velocity: 0.5
angular_velocity: 0.30000001192092896
```

Черепаха едет по окружности радиуса v/ω = 0,5/0,3 ≈ 1,67; поза меняется,
скорости в позе равны отправленным 0,5 и 0,3.

### Частота команды (≈10 с)

```text
$ timeout --signal=INT 10s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
average rate: 9.997
	min: 0.094s max: 0.106s std dev: 0.00205s window: 11
...
average rate: 9.999
	min: 0.094s max: 0.106s std dev: 0.00193s window: 89
```

Измерено ≈10,0 Гц, что соответствует периоду таймера 0,1 с (джиттер ±6 мс).

## Остановка

B: Ctrl+C → `[ros2run]: Received signal: Interrupt`, процесс завершился с кодом 0.
Через 2 с:

```text
$ ros2 topic echo /turtle1/pose --once
x: 5.226358413696289
y: 5.5743021965026855
theta: -0.19198529422283173
linear_velocity: 0.0
angular_velocity: 0.0

$ ros2 node list --no-daemon --spin-time 2
/turtlesim
```

Черепаха остановилась (скорости 0) не от «команды остановки», а потому что
новые Twist перестали приходить. Симулятор продолжает работать.

## Тесты

`src/patrol/test/test_command.py` проверяет чистую функцию без ROS: отсутствие
позы → нулевая команда, обычная поза → (0.5, 0.3), независимость от координат,
ограничение ±1. Полный вывод — `tests.txt`: прямой pytest из каталога пакета
`9 passed, 1 skipped` (пропущен только сгенерированный `test_copyright`),
`colcon test-result`: `10 tests, 0 errors, 0 failures, 1 skipped`.
