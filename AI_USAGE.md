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
