"""
Чистая логика SceneDescription v1: проверка, канонический unknown, ключ кэша.

Модуль не зависит от rclpy, поэтому тестируется обычным pytest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Optional

from jsonschema import Draft202012Validator

SCHEMA_VERSION = 1
DEFAULT_ABSTAIN_THRESHOLD = 0.5
DEFAULT_MAX_AGE_S = 0.25

REASON_INVALID_SCHEMA = 'invalid_schema'
REASON_LOW_CONFIDENCE = 'low_confidence'
REASON_STALE_INPUT = 'stale_input'

Scene = dict[str, Any]


def load_schema(path: Path) -> dict[str, Any]:
    """Прочитать JSON Schema из файла."""
    return json.loads(Path(path).read_text(encoding='utf-8'))


def canonical_unknown(raw: Any, reason: str, source: str) -> Scene:
    """
    Построить канонический unknown.

    Сохраняются только допустимые stamp_s и frame_id исходного наблюдения;
    категории unknown, расстояния null, confidence 0.
    """
    stamp = 0.0
    frame = 'base_link'
    if isinstance(raw, dict):
        value = raw.get('stamp_s')
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            stamp = float(value)
        value = raw.get('frame_id')
        if isinstance(value, str) and value:
            frame = value
    return {
        'version': SCHEMA_VERSION,
        'stamp_s': stamp,
        'frame_id': frame,
        'status': 'unknown',
        'status_reason': reason,
        'lane_offset_m': 0.0,
        'traffic_light': 'unknown',
        'direction_sign': 'unknown',
        'stop_line_distance_m': None,
        'turn_distance_m': None,
        'obstacle_distance_m': None,
        'confidence': 0.0,
        'source': source,
    }


def evaluate_scene(raw: Any, schema: dict[str, Any], *, now_s: float,
                   source: str,
                   abstain_threshold: float = DEFAULT_ABSTAIN_THRESHOLD,
                   max_age_s: float = DEFAULT_MAX_AGE_S) -> Scene:
    """
    Превратить сырой ответ в публичный результат.

    Порядок: схема (в т.ч. запрет лишних полей, например drive) → возраст →
    уверенность. Любая ошибка даёт канонический unknown с причиной.
    """
    if not Draft202012Validator(schema).is_valid(raw):
        return canonical_unknown(raw, REASON_INVALID_SCHEMA, source)
    scene: Scene = dict(raw)
    scene['source'] = source
    if scene['status'] == 'unknown':
        return scene
    if now_s - float(scene['stamp_s']) > max_age_s:
        return canonical_unknown(scene, REASON_STALE_INPUT, source)
    if float(scene['confidence']) < abstain_threshold:
        return canonical_unknown(scene, REASON_LOW_CONFIDENCE, source)
    return scene


def sha256_file(path: Path) -> str:
    """SHA-256 содержимого файла (hex)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key_payload(image_sha256: str, prompt_sha256: str, model_id: str,
                generation_config: dict[str, Any]) -> dict[str, Any]:
    """Полный набор входов VLM, от которых зависит ответ."""
    return {
        'image_sha256': image_sha256,
        'prompt_sha256': prompt_sha256,
        'model_id': model_id,
        'generation_config': generation_config,
        'schema_version': SCHEMA_VERSION,
    }


def cache_key(image_sha256: str, prompt_sha256: str, model_id: str,
              generation_config: dict[str, Any]) -> str:
    """SHA-256 от JSON с отсортированными ключами и без лишних пробелов."""
    payload = key_payload(image_sha256, prompt_sha256, model_id, generation_config)
    text = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


Backend = Callable[[str, str, str, dict[str, Any]], Any]
"""backend(image_sha256, prompt_text, model_id, generation_config) -> сырой JSON."""


class SceneCache:
    """Кэш сырых ответов VLM на диске: <cache_dir>/<key>.json."""

    def __init__(self, cache_dir: Path, backend: Optional[Backend] = None,
                 key_fn: Callable[..., str] = cache_key) -> None:
        self.cache_dir = Path(cache_dir)
        self.backend = backend
        self.key_fn = key_fn
        self.backend_calls = 0

    def get(self, image_sha256: str, prompt_path: Path, model_id: str,
            generation_config: dict[str, Any]) -> tuple[Any, bool]:
        """Вернуть (сырой ответ, hit). При промахе вызывает backend и сохраняет ответ."""
        prompt_sha = sha256_file(prompt_path)
        key = self.key_fn(image_sha256, prompt_sha, model_id, generation_config)
        path = self.cache_dir / f'{key}.json'
        if path.is_file():
            return json.loads(path.read_text(encoding='utf-8')), True
        if self.backend is None:
            raise RuntimeError('cache miss и backend не настроен: сетевой вызов не выполняется')
        self.backend_calls += 1
        raw = self.backend(image_sha256, Path(prompt_path).read_text(encoding='utf-8'),
                           model_id, generation_config)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(raw, ensure_ascii=False, sort_keys=True), encoding='utf-8')
        return raw, False
