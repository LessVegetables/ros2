# ПР02. Топики и типы turtlesim

Типы взяты из вывода `ros2 topic type` / `ros2 topic info` в ROS 2 Lyrical.

| Топик | Тип | Направление | Назначение |
|-------|-----|-------------|------------|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | издатель (teleop, `ros2 topic pub`) → `/turtlesim` | команда скорости для `turtle1` |
| `/turtle1/pose` | `turtlesim_msgs/msg/Pose` | `/turtlesim` → наблюдатели | текущее положение и скорость `turtle1` |

В Jazzy тип позы называется `turtlesim/msg/Pose`, в Lyrical — `turtlesim_msgs/msg/Pose`.

## `geometry_msgs/msg/Twist`

```text
$ ros2 interface show geometry_msgs/msg/Twist
# This expresses velocity in free space broken into its linear and angular parts.

Vector3  linear
        float64 x
        float64 y
        float64 z
Vector3  angular
        float64 x
        float64 y
        float64 z
```

Twist описывает скорость тела в пространстве, а не положение и не перемещение.

| Поле | Смысл | Использование в turtlesim |
|------|-------|---------------------------|
| `linear.x` | линейная скорость вперёд по курсу | ход вперёд/назад |
| `linear.y` | линейная скорость вбок | не используется: черепаха не ходит боком |
| `linear.z` | линейная скорость вверх | не используется: мир плоский |
| `angular.x`, `angular.y` | угловая скорость вокруг осей x и y (крен, тангаж) | не используются |
| `angular.z` | угловая скорость вокруг вертикальной оси (рыскание), рад/с, + — против часовой стрелки | поворот |

Команда опыта `{linear: {x: 1.0}, angular: {z: 0.5}}` означает «вперёд со
скоростью 1 и поворот 0,5 рад/с». В результате черепаха движется по дуге
радиусом v/ω = 2. Не указанные в YAML поля равны 0. turtlesim выполняет
последнюю команду примерно 1 с, поэтому `--once` даёт короткую дугу, а
`--rate 1` — непрерывное движение по окружности.

## `turtlesim_msgs/msg/Pose`

| Поле | Смысл |
|------|-------|
| `x`, `y` | положение черепахи в окне (0…≈11; старт ≈ 5,54) |
| `theta` | курс в радианах, 0 — вдоль оси x, + — против часовой стрелки |
| `linear_velocity` | текущая линейная скорость |
| `angular_velocity` | текущая угловая скорость |

Пример из опыта, во время движения по окружности: `x: 7.43, y: 8.18,
theta: 1.89, linear_velocity: 1.0, angular_velocity: 0.5`. Скорости в позе
совпадают с полями `linear.x` и `angular.z` полученного Twist.
