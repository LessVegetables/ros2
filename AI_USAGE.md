# Декларация использования ИИ

## PR01

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).

| Модель | Инструмент / среда | Компонент | Характер помощи | Как проверено |
|--------|--------------------|-----------|-----------------|---------------|
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `README.md`, `.github/workflows/ci.yml`, `.gitignore` | подготовка порядка запуска в Docker, workflow CI по образцу курса | команды выполнены вручную в контейнере; JSON и checker курса запущены локально |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `evidence/pr01/graph.md`, `environment.json`, `report.json` | оформление отчёта по выводам команд, которые я получил сам; объяснение причины разрыва | все выводы в отчёте получены мной в живом опыте (`doctor.txt`, `pose-*.txt` записаны командами); текст сверен с терминалом и наблюдением за черепахой |

Логи и измерения ИИ не генерировал: команды ROS 2 запускал я, ИИ только
оформил их результаты.

## PR02

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).

| Модель | Инструмент / среда | Компонент | Характер помощи | Как проверено |
|--------|--------------------|-----------|-----------------|---------------|
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `src/turtle_bringup` (`package.xml`, `setup.py`, `launch/sim.launch.py`) | метаданные пакета, запись `data_files`, launch-файл по образцу из условия; каркас создан мной через `ros2 pkg create` | сборка `colcon build` (`build.txt`), установленный `sim.launch.py` найден, `ros2 launch` запускает и останавливает turtlesim, `py_compile` |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `.github/workflows/ci.yml`, `README.md`, `.gitignore` | шаг сборки пакета в CI по инструкции курса, порядок запуска | локальная сборка и checker курса; CI на GitHub |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `evidence/pr02/commands.md`, `types.md`, `report.json` | список команд для опыта, оформление отчёта по моим выводам терминала | все команды ROS 2 выполнены мной; выводы и наблюдения в отчёте сверены с терминалами и окном TurtleSim |

Логи и измерения ИИ не генерировал: команды ROS 2 запускал я, ИИ только
оформил их результаты.

## PR03

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).

| Модель | Инструмент / среда | Компонент | Характер помощи | Как проверено |
|--------|--------------------|-----------|-----------------|---------------|
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app), команды в контейнере через `docker exec` | `src/patrol` (`package.xml`, `setup.py`, `patrol/patrol.py`, `patrol/command.py`, `test/test_command.py`) | написал ноду с подпиской и таймером, чистую функцию выбора команды и её тесты | `colcon test`: 10 тестов, 0 ошибок, 1 пропуск (`test_copyright`); поведение — опыт без remap / с remap и `topic hz` |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `.github/workflows/ci.yml`, `README.md` | перевод CI на образ Lyrical из инструкции курса, полный `colcon build/test`, kit v1-w12 | локальная сборка и checker курса; CI на GitHub |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app), `docker exec` в контейнер `ros2` | `evidence/pr03/demo.md`, `tests.txt`, `report.json` | **запустил опыт сам** (turtlesim, patrol без remap и с remap, `ros2 topic hz`, тесты) и оформил отчёт по полученным выводам | выводы в отчёте — реальные выводы команд этого прогона (скриншоты окна в `lab3/`); сценарий воспроизводится командами из `README.md` |

В отличие от PR01–PR02, команды ROS 2 для evidence этой ПР запускал ИИ-агент
в моём контейнере; выводы не редактировались, только сокращены повторяющиеся
строки.

## PR04

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).

| Модель | Инструмент / среда | Компонент | Характер помощи | Как проверено |
|--------|--------------------|-----------|-----------------|---------------|
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `src/patrol` (`patrol.py`, `command.py`, `test/test_parameters.py`, `test/test_node_parameters.py`) | параметры с проверкой в on_set-callback и пересозданием таймера в post_set-callback, чистые функции проверки, тесты; дефектный вариант для опыта | `colcon test`: 46 тестов, 0 ошибок, 1 пропуск; тот же тест на дефектном коде: 4 failed |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app), `docker exec` в контейнер `ros2` | `evidence/pr04/parameters.md`, `tests.txt`, `report.json` | **запустил опыт сам**: `ros2 param set/get`, `topic hz` до и после, дефект с нулевой частотой, `/clear`, `rotate_absolute`; оформил отчёт по выводам | выводы — реальные выводы этого прогона; сценарий воспроизводится командами из `README.md` |

Команды ROS 2 для evidence этой ПР запускал ИИ-агент в моём контейнере;
выводы не редактировались, только сокращены повторяющиеся строки.

## PR05

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).

| Модель | Инструмент / среда | Компонент | Характер помощи | Как проверено |
|--------|--------------------|-----------|-----------------|---------------|
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `src/course_bringup` (`launch/patrol.launch.py`, тест launch), `src/patrol` (`pose_relay.py`, `pose_subscriber.py`, `qos.py`, `test/test_qos.py`), `config/qos-overrides.yaml` | launch с аргументами, namespace, remap и записью по `IfCondition`; ноды ретранслятора и подписчика с настраиваемым QoS | `colcon test`: 57 тестов, 0 ошибок, 2 пропуска (copyright) |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app), `docker exec` в контейнер `ros2` | `evidence/pr05/*` (логи QoS, запись MCAP, `bag-metadata.yaml`, `notes.md`, `report.json`) | **запустил опыт сам**: reliable/best_effort на живом потоке, запись, повтор с override, `record:=true`; оформил разбор | выводы и запись — реальные результаты этого прогона; сценарий воспроизводится командами из `README.md` |

Команды ROS 2 для evidence этой ПР запускал ИИ-агент в моём контейнере;
выводы не редактировались.

## PR06

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).

| Модель | Инструмент / среда | Компонент | Характер помощи | Как проверено |
|--------|--------------------|-----------|-----------------|---------------|
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `src/course_description` (`urdf/vehicle.urdf.xacro`, `launch/display.launch.py`, `rviz/vehicle.rviz`, `test/test_description.py`) | Xacro-модель по размерам SDF из course kit, макросы инерции, launch robot_state_publisher + RViz, структурные тесты; дефектный вариант parent лидара | `check_urdf`, `colcon test`: 70 тестов, 0 ошибок; тест parent падает на дефекте (2 failed) |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app), `docker exec` в контейнер `ros2` | `evidence/pr06/*`, скриншоты RViz и графы `view_frames` в `lab6/` | **запустил опыт сам**: QoS /tf_static, tf2_echo, view_frames, дефект и исправление; оформил таблицу frames | выводы — реальные результаты этого прогона; RViz осмотрен по скриншотам `lab6/` |

Команды ROS 2 для evidence этой ПР запускал ИИ-агент в моём контейнере;
выводы не редактировались, только сокращены повторяющиеся строки.

## PR07

- Использован ИИ: да (`ai_used: true` в отчёте этой ПР).

| Модель | Инструмент / среда | Компонент | Характер помощи | Как проверено |
|--------|--------------------|-----------|-----------------|---------------|
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app) | `src/course_simulation` (launch, `drive_adapter`, `odom_adapter`, `drive_source`, тесты; копии модели, мира и моста из kit с изменениями ПР07), шаг `apt-get upgrade` в CI | код адаптеров по контракту `contracts/topics.md`, headless-launch, QoS SENSOR_DATA в мосте | `colcon test` пакета; живой прогон в Gazebo |
| Claude Opus 5.5 (`claude-opus-5-5`) | Claude Code (desktop app), `docker exec` в контейнер `ros2` | `evidence/pr07/*` | **запустил опыт сам**: обновил пакеты контейнера (`apt-get upgrade`, ackermann_msgs), headless-запуск, частоты, команда на обеих сторонах моста, запись, дефект моста; оформил отчёт | выводы — реальные результаты прогона; запись (353 МиБ) хранится вне Git |

Команды ROS 2 / Gazebo для evidence этой ПР запускал ИИ-агент в моём контейнере.
