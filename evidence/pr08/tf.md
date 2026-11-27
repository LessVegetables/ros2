# ПР08. Цепочка map → odom → base_link → lidar_link

Вход: запись ПР07 `/home/ubuntu/bags/pr07-sensors` (35,8 с по `/clock`, прямое
движение 0,2 м/с от (0, 0) до x ≈ 7,3 м; копия на SSD хоста). Карта —
`.course-kit/v1/fixtures/pr08/map.{yaml,pgm}` (копия в `evidence/pr08/`),
SHA-256: yaml `79d1003f…66cc0`, pgm `f190d3ec…549de`. Начальная поза (0, 0, 0).
При replay проигрываются только `/vehicle/scan /vehicle/odom /tf /tf_static /clock`
(сама запись не меняется); Gazebo, мост и адаптеры не запущены.

## Владельцы преобразований

| Связь | Владелец | Топик | Откуда во время replay |
|---|---|---|---|
| `map → odom` | `amcl` | `/tf`, dynamic | живой AMCL (единственный) |
| `odom → base_link` | `odom_adapter` ПР07 | `/tf`, dynamic | из записи (адаптер не запускается) |
| `base_link → lidar_link` | `robot_state_publisher` ПР06 | `/tf_static`, static | из записи |

`view_frames` при исправленном запуске (`run.txt`, `frames.pdf`):
`map→odom` ≈ 10 Гц, `odom→base_link` ≈ 50 Гц, статические `base_link→{camera,imu,lidar}_link`.

## Команда и ошибка до исправления (`defect.txt`)

`evidence/pr08/amcl-defect.yaml` — копия профиля, изменён только
`base_frame_id: chassis`.

```text
$ ros2 launch localization_case localization.launch.py params_file:=$PWD/evidence/pr08/amcl-defect.yaml map:=$PWD/.course-kit/v1/fixtures/pr08/map.yaml
$ ros2 lifecycle get /amcl
active [3]
[amcl] [ERROR]: Couldn't transform from lidar_link to chassis, even though the message notifier is in use: ("chassis" passed to lookupTransform argument target_frame does not exist. )
$ ros2 run tf2_ros tf2_echo map odom --ros-args -p use_sim_time:=true
Waiting for transform map ->  odom: Invalid frame ID "map" passed to canTransform argument target_frame - frame does not exist
$ timeout --signal=INT 4 ros2 topic echo /amcl_pose --once      → сообщений нет
[measure_localization]: map→odom недоступно: "map" passed to lookupTransform argument target_frame does not exist.
```

Ноды активны (карта и lifecycle в порядке), но AMCL не может выразить скан
(`lidar_link`) в системе робота `chassis`, которой нет в дереве. Без этого он
не обновляет фильтр, не публикует `/amcl_pose` и, главное, не публикует
`map → odom` — поэтому frame `map` вообще отсутствует в tf. Причина в
`base_frame_id`, а не в карте или установке Nav2: карта, запись и пакеты те же.

## После исправления (`run.txt`, `localization.json`)

`base_frame_id: base_link`, та же карта, запись, начальная поза и окно:

```text
$ ros2 lifecycle get /map_server  → active [3]
$ ros2 lifecycle get /amcl        → active [3]
$ ros2 run tf2_ros tf2_echo map odom --ros-args -p use_sim_time:=true
At time 38.300000000
- Translation: [-0.215, 0.022, 0.000]
- Rotation: in RPY (degree) [0.000, 0.000, -1.129]
$ ros2 run tf2_ros tf2_echo map lidar_link --ros-args -p use_sim_time:=true
At time 40.197000000
- Translation: [4.002, -0.079, 0.380]
```

Измерение (`measure_localization.py`, запущен до player, t0 = 20.354 с — первый
`/clock`; окно [30.354; 50.354) по времени записи, шаг 0,1 с):

| Метрика | Значение | Порог |
|---|---:|---:|
| запросов `lookup_transform('map','odom', Time())` | 200 | 200 |
| успешных | 200 | ≥ 190 |
| доступность | 1.000 | ≥ 0.95 |
| `/amcl_pose` в окне | 66 | ≥ 10 |
| медиана cov[0]+cov[7] | 0.0427 м² | ≤ 0.25 |

`validate_localization.py`: «схема, метрики и SHA-256 карты корректны» (`schema-check.txt`).

## Сопоставление времени

Один момент replay: `/vehicle/scan` stamp 50.300, `/vehicle/odom` 51.437,
`/clock` 52.505 — все в шкале записанного `/clock`, скан отстаёт на ~1–2 с
только из-за последовательного выполнения трёх команд `echo`. AMCL и
измеритель используют `use_sim_time=true`, поэтому `map→odom` (stamp 38.3 при
`/amcl_pose` 34.5) лежит на той же шкале, что и данные записи.

## Ограничения

Доступность `map→odom` и малая ковариация — критерии сходимости и уверенности
AMCL, а не точности: независимой ground truth в ПР08 нет. Уверенная, но
неверная поза тоже возможна; дополнительно стоит сравнить наложение
`/vehicle/scan` на стены `/map` в RViz. Здесь косвенная проверка — поза AMCL
x ≈ 2,6 м на 34,5 с согласуется с движением 0,2 м/с от старта.
