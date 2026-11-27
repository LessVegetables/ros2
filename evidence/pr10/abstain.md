# ПР10. Отказ (unknown) и ключ кэша

## Выбранные пороги

`config/vlm.yaml`: `abstain_threshold: 0.5`, `max_age_s: 0.25` — как в
`fixtures/vlm/README.md` курса. Возраст = `now_s − stamp_s` по ROS-часам ноды
(`use_sim_time` + `/clock` в демонстрации, явный `now_s` в unit-тестах). Чтение
mock/кэша сохраняет исходный `stamp_s`; попадание в кэш проверяется по возрасту
повторно (`test_cache_hit_is_rechecked_for_age`).

## Ожидаемые причины отказа (`schema-check.txt`, `ros-demo.txt`)

| Fixture | now_s | Сырой ответ по схеме | Итог | status_reason |
|---|---:|---|---|---|
| `scene-clear.json` | 0.1 | ok | valid | `""` |
| `scene-low-confidence.json` | 0.1 | ok (confidence 0.24) | unknown | `low_confidence` |
| `scene-stale.json` | 2.0 | ok (stamp_s 1.0, возраст 1.0 > 0.25) | unknown | `stale_input` |
| `scene-extra-command.json` | 0.1 | **ошибка**: `Additional properties are not allowed ('drive' was unexpected)` | unknown | `invalid_schema` |

Канонический unknown: категории `unknown` (в ROS — 255), расстояния `null`
(`has_* = false`, число 0.0), `confidence = 0`, допустимые `stamp_s` и
`frame_id` исходного наблюдения сохраняются. Поле `drive` отклоняет весь ответ —
дальше адаптера команда не проходит. Неизвестное значение enum при
преобразовании в ROS — ошибка адаптера → `invalid_schema`.
`mode=live` без внедрённого backend завершается `RuntimeError` без сетевого
вызова; промах кэша без backend — явная ошибка.

## Ключ кэша

SHA-256 от UTF-8 JSON (`sort_keys=True`, `separators=(',', ':')`) с полями
`image_sha256`, `prompt_sha256` (хэш фактически прочитанного файла промпта),
`model_id`, `generation_config` (целиком), `schema_version: 1`.

### Наблюдаемая коллизия дефектного кэша (`defect.txt`)

В дефектном варианте (`labs/pr10/defect.patch`) из ключа убран `prompt_sha256`.
Ключи для промптов `bbbb…` и `dddd…` совпали:

```text
assert '7afa5eb54362fc99…0e7d67fd98636c' != '7afa5eb54362fc99…0e7d67fd98636c'
FAILED test_each_component_changes_key[prompt_sha256-…]
FAILED test_every_component_misses[prompt] - assert (True is False)
```

То есть после смены файла промпта кэш вернул **старую** сцену (hit=True,
backend не вызывался) — ответ на другой вопрос выдан за актуальный. После
возврата полного ключа: `22 passed`, изменение каждого из пяти компонентов
(image, prompt, model, config, а schema_version — константа контракта) даёт
промах и новый вызов backend (счётчик вызовов растёт).
