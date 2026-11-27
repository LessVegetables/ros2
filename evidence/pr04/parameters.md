# ПР04. Параметризуем движение

Среда: Docker `tiryoh/ros2-desktop-vnc` (ROS 2 Lyrical), домен 26,
`ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST`. A — `ros2 launch turtle_bringup sim.launch.py`,
B — `ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel`, C — команды ниже.

## Параметры patrol

| Параметр | По умолчанию | Допустимо | Что меняет |
|----------|--------------|-----------|------------|
| `linear_speed` | 0.5 м/с | конечное, 0…1 | `linear.x` команды |
| `turn_rate` | 0.3 рад/с | конечное, −1…1 | `angular.z` команды |
| `publish_hz` | 10.0 Гц | конечное, 1…30 | период таймера `1/publish_hz` |

Устройство (`src/patrol/patrol/patrol.py`):

1. `add_on_set_parameters_callback` — **проверка до применения**. Вызывает чистую
   функцию `validate_parameter` (`patrol/command.py`). При ошибке возвращает
   `SetParametersResult(successful=False, reason=...)`: значение параметра,
   таймер и скорости не меняются.
2. `add_post_set_parameters_callback` — **применение принятого значения**. Для
   `publish_hz` сначала вычисляется новый период, затем старый таймер
   уничтожается (`destroy_timer`) и создаётся новый. Двух таймеров одновременно
   не бывает (это проверяет `test_valid_rate_recreates_single_timer`:
   `len(node.timers) == 1`).

## Опыт с исправной нодой

```text
$ ros2 param list /patrol --no-daemon --spin-time 2
  linear_speed
  publish_hz
  start_type_description_service
  turn_rate
  use_sim_time

$ ros2 param get /patrol linear_speed / turn_rate / publish_hz
Double value is: 0.5
Double value is: 0.3
Double value is: 10.0

$ timeout --signal=INT 10s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
average rate: 9.998
	min: 0.060s max: 0.139s std dev: 0.00661s window: 79
```

### Допустимое изменение 10 → 5 Гц

```text
$ ros2 param set /patrol publish_hz 5.0 --no-daemon --spin-time 2
Set parameter successful

$ ros2 param get /patrol publish_hz --no-daemon --spin-time 2
Double value is: 5.0

$ timeout --signal=INT 10s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
average rate: 5.001
	min: 0.197s max: 0.203s std dev: 0.00157s window: 44
```

Лог B: `publish_hz=5.0: таймер пересоздан, период 0.200 с`. Поток стал 5 Гц
без перезапуска ноды.

### Недопустимые значения отклонены, состояние сохранено

```text
$ ros2 param set /patrol publish_hz 10.0 --no-daemon --spin-time 2
Set parameter successful

$ ros2 param set /patrol publish_hz 0.0 --no-daemon --spin-time 2
Setting parameter failed: publish_hz=0.0 вне диапазона [1.0, 30.0]

$ ros2 param set /patrol publish_hz -1.0 --no-daemon --spin-time 2
Setting parameter failed: publish_hz=-1.0 вне диапазона [1.0, 30.0]

$ ros2 param set /patrol publish_hz .nan --no-daemon --spin-time 2
Setting parameter failed: publish_hz: ожидается конечное число, получено nan

$ ros2 param get /patrol publish_hz --no-daemon --spin-time 2
Double value is: 10.0

$ timeout --signal=INT 10s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
average rate: 9.997
	min: 0.095s max: 0.105s std dev: 0.00157s window: 79
```

Значение осталось 10.0, поток продолжается с той же частотой, нода жива.

### Скорость и поворот

```text
$ ros2 param set /patrol linear_speed 0.8 --no-daemon --spin-time 2
Set parameter successful
$ ros2 param set /patrol turn_rate 0.6 --no-daemon --spin-time 2
Set parameter successful
$ ros2 topic echo /turtle1/pose --once
x: 3.841008424758911
y: 5.620114326477051
theta: -0.12952649593353271
linear_velocity: 0.800000011920929
angular_velocity: 0.6000000238418579

$ ros2 param set /patrol linear_speed 2.0 --no-daemon --spin-time 2
Setting parameter failed: linear_speed=2.0 вне диапазона [0.0, 1.0]
$ ros2 param get /patrol linear_speed --no-daemon --spin-time 2
Double value is: 0.8
```

Лог B за весь опыт:

```text
[INFO] [patrol]: patrol: поза из /turtle1/pose, команда в /turtle1/cmd_vel, linear_speed=0.5, turn_rate=0.3, publish_hz=10.0
[INFO] [patrol]: publish_hz=5.0: таймер пересоздан, период 0.200 с
[INFO] [patrol]: publish_hz=10.0: таймер пересоздан, период 0.100 с
[WARN] [patrol]: отклонено: publish_hz=0.0 вне диапазона [1.0, 30.0]
[WARN] [patrol]: отклонено: publish_hz=-1.0 вне диапазона [1.0, 30.0]
[WARN] [patrol]: отклонено: publish_hz: ожидается конечное число, получено nan
[WARN] [patrol]: отклонено: linear_speed=2.0 вне диапазона [0.0, 1.0]
```

## Дефект: проверка частоты временно отключена

Отдельное изменение (файл `defect.patch` вне репозитория, в рабочей ветке не
сохраняется) — в `_on_set_parameters` пропускается проверка `publish_hz`:

```python
for param in params:
    if param.name == 'publish_hz':
        continue  # ДЕФЕКТ ПР04: проверка частоты временно отключена
    reason = validate_parameter(param.name, param.value)
```

### Живой отказ

```text
$ ros2 param get /patrol publish_hz --no-daemon --spin-time 2
Double value is: 10.0
$ timeout --signal=INT 6s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
average rate: 9.585

$ ros2 param set /patrol publish_hz 0.0 --no-daemon --spin-time 2
(ответа нет: команда ждёт ответа сервиса, прервана Ctrl+C, exit=2)

$ ros2 node list --no-daemon --spin-time 2
/turtlesim

$ ros2 param get /patrol publish_hz --no-daemon --spin-time 2
Node not found

$ timeout --signal=INT 6s ros2 topic hz /turtle1/cmd_vel --qos-reliability reliable
(ни одного сообщения, exit=124)
```

Лог B (сокращён):

```text
Traceback (most recent call last):
  ...
  File ".../rclpy/parameter_service.py", line 142, in _set_parameters_callback
    result = node.set_parameters_atomically([param])
  ...
  File ".../rclpy/node.py", line 1038, in _call_post_set_parameters_callback
    callback(parameter_list)
  File ".../patrol/patrol.py", line 84, in _on_parameters_set
    period = period_for(float(param.value))
  File ".../patrol/command.py", line 93, in period_for
    return 1.0 / publish_hz
ZeroDivisionError: division by zero
[ros2run]: Process exited with failure 1
```

Ноль прошёл проверку, параметр был принят, и при вычислении периода
`1/publish_hz` в callback применения возникло деление на ноль. Исключение
поднялось из обработчика сервиса `set_parameters` через `rclpy.spin`: нода
упала, поток команд прекратился, клиент `param set` так и не получил ответ.

### Тот же тест до и после

`src/patrol/test/test_node_parameters.py::test_invalid_rate_rejected_state_kept`
создаёт живую ноду `Patrol` и вызывает `set_parameters` с недопустимой
частотой. На дефектном коде:

```text
$ (cd src/patrol && python3 -m pytest test/test_node_parameters.py -q --tb=line)
E   ZeroDivisionError: division by zero
/home/ubuntu/ros2_local/src/patrol/patrol/command.py:93: ZeroDivisionError: division by zero
E   rclpy._rclpy_pybind11.RCLError: failed to create timer: timer period must be non-negative, at ./src/rcl/timer.c:117
E   ValueError: cannot convert float NaN to integer
E   AssertionError: assert not True
/home/ubuntu/ros2_local/src/patrol/test/test_node_parameters.py:45: AssertionError: assert not True
FAILED test/test_node_parameters.py::test_invalid_rate_rejected_state_kept[0.0]
FAILED test/test_node_parameters.py::test_invalid_rate_rejected_state_kept[-1.0]
FAILED test/test_node_parameters.py::test_invalid_rate_rejected_state_kept[nan]
FAILED test/test_node_parameters.py::test_invalid_rate_rejected_state_kept[31.0]
4 failed, 3 passed in 0.44s
```

Разные значения ломают по-разному: 0 → деление на ноль; −1 → период
отрицательный, и `create_timer` падает **после** `destroy_timer` — нода
остаётся вовсе без таймера; NaN → ошибка преобразования периода; 31 Гц
молча принимается вне контракта.

После возврата проверки тот же файл: `7 passed`. Полный прогон — `tests.txt`
(`45 passed, 1 skipped`; `colcon test-result`: `46 tests, 0 errors, 0 failures, 1 skipped`).

**Почему исправление правильное.** Вход проверяется в `on_set`-callback **до**
изменения параметра, таймера и скоростей; отказ возвращается клиенту как
`Setting parameter failed: <причина>`. Применение (`post_set`) получает только
уже проверенные значения, поэтому `1/publish_hz` всегда определено, а старый
таймер уничтожается лишь тогда, когда новый период уже вычислен.

## Сервис и действие turtlesim

```text
$ ros2 service type /clear
std_srvs/srv/Empty
$ ros2 service call /clear std_srvs/srv/Empty "{}" --timeout 5
requester: making request: std_srvs.srv.Empty_Request()
response:
std_srvs.srv.Empty_Response()

$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim_msgs/action/RotateAbsolute]
$ ros2 action info /turtle1/rotate_absolute
Action: /turtle1/rotate_absolute
Action clients: 0
Action servers: 1
    /turtlesim
$ ros2 interface show turtlesim_msgs/action/RotateAbsolute
# The desired heading in radians
float32 theta
---
# The angular displacement in radians to the starting position
float32 delta
---
# The remaining rotation in radians
float32 remaining

$ ros2 action send_goal /turtle1/rotate_absolute turtlesim_msgs/action/RotateAbsolute "{theta: 1.57}" --feedback
Goal accepted with ID: 11bbe562d1154a59ac20dec99bf2d240
Feedback:
    remaining: 1.5700000524520874
Feedback:
    remaining: 1.5540000200271606
...
Result:
    delta: -1.5520000457763672
Goal finished with status: SUCCEEDED
```

**Запрос и цель.** Сервис `/clear` — один запрос и один ответ: клиент ждёт,
сервер сразу выполняет короткую операцию и отвечает. Действие
`/turtle1/rotate_absolute` принимает цель (`theta`), долго её исполняет,
по ходу шлёт обратную связь (`remaining`), может быть отменено и в конце
возвращает результат (`delta`) со статусом.
