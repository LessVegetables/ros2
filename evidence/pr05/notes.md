# ПР05. Launch, QoS и повтор записи — разбор

Файлы: `qos-before.txt` (сбой), `qos-after.txt` (исправление, запись, повтор,
`ros2 bag info`, проверка `record:=true`), `bag-metadata.yaml` (копия
`bag/metadata.yaml`), сама запись — `bag/` (MCAP, 72 КиБ, 972 сообщения).

## Система одной командой

`ros2 launch course_bringup patrol.launch.py namespace:=robot_a subscriber_reliability:=<reliable|best_effort> record:=<true|false> bag_dir:=<путь>`

| Нода | Полное имя | Вход | Выход |
|------|-----------|------|-------|
| turtlesim (глобально) | `/turtlesim` | `/turtle1/cmd_vel` | `/turtle1/pose` |
| patrol | `/robot_a/patrol` | `turtle1/pose` → remap `/turtle1/pose` | `cmd_vel` → remap `/turtle1/cmd_vel` |
| pose_relay | `/robot_a/pose_relay` | `pose` → remap `/turtle1/pose` | `sensor_pose` = `/robot_a/sensor_pose`, **best_effort** |
| pose_subscriber | `/robot_a/pose_subscriber` | `sensor_pose` = `/robot_a/sensor_pose`, reliability из аргумента | — |
| recorder (только при `record:=true`, `IfCondition`) | `ros2 bag record -s mcap` | `/<namespace>/sensor_pose` | `bag_dir` |

Имена внутри нод относительные; namespace добавляет `PushRosNamespace`, а
remap в launch соединяет их с единственным глобальным turtlesim.

## Причина сбоя

Издатель `pose_relay` предлагает `BEST_EFFORT`, подписчик запрашивает
`RELIABLE`. Запрашиваемая надёжность не может быть выше предлагаемой, поэтому
DDS не связывает эти конечные точки: топик и обе стороны видны в
`ros2 topic info --verbose`, тип совпадает, но доставки нет. Об этом пишут обе
стороны: `pose_relay` — «requesting incompatible QoS. No messages will be sent
to it», `pose_subscriber` — событие `incompatible_qos` с
`RMW_QOS_POLICY_RELIABILITY`; `ros2 topic echo --qos-reliability reliable`
завершился по таймауту (`exit=124`).

## Исправление и проверка на той же записи

Подписчик переведён на `best_effort` (аргумент launch, код не менялся):
`pose_subscriber` получает позы (`count=1, 20, 40…`), `echo` с best_effort
печатает позу (`exit=0`). Записан один поток `/robot_a/sensor_pose`
(15,5 с, 972 сообщения ≈ 62,5 Гц, как публикует turtlesim).

Повтор `ros2 bag play ... --qos-profile-overrides-path config/qos-overrides.yaml`
без живой системы: издатель — `/rosbag2_player` с тем же профилем
`BEST_EFFORT, KEEP_LAST(10)`. На этой одной записи reliable-подписчик снова не
получает сообщений (`exit=124`), best_effort — получает (`exit=0`). Значит, «до» и
«после» проверены на одном наборе входных сообщений, и причина — только профиль
QoS. Без override player публиковал бы с профилем по умолчанию, и проверка
reliable-подписчика на повторе дала бы другой результат, чем на живом потоке.

MCAP хранит сообщения и их время, но не версии кода и аргументы запуска —
их фиксируют `report.json` (commit) и команды выше.

## Запуск без ручных шагов

`record:=true` запускает recorder из самого launch (`IfCondition`), запись
`/tmp/pr05-launch-bag`: 447 сообщений за 7,1 с. При `record:=false` процесс
`ros2 bag record` не создаётся (тест `test_recorder_runs_only_when_record_true`).

Примечание о `timeout`: в Lyrical `ros2 topic echo` перехватывает SIGTERM и
продолжает ждать, поэтому в опыте использован `timeout --signal=INT 3s` —
ожидаемый `exit=124` сохраняется.
