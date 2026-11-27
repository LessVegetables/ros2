"""Offline-тесты адаптера: четыре fixtures, unknown, ключ кэша (без сети и ROS)."""

import json
from pathlib import Path

import pytest

from scene_adapter.core import (
    cache_key, canonical_unknown, evaluate_scene, load_schema, SceneCache, sha256_file,
)

PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parents[1]
SCHEMA = load_schema(ROOT / 'contracts' / 'scene-description-v1.schema.json')
FIXTURES = ROOT / 'fixtures' / 'vlm'
THRESHOLD = 0.5
MAX_AGE = 0.25


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding='utf-8'))


def run(name: str, now_s: float) -> dict:
    return evaluate_scene(fixture(name), SCHEMA, now_s=now_s, source='mock',
                          abstain_threshold=THRESHOLD, max_age_s=MAX_AGE)


@pytest.mark.parametrize('name,now_s,status,reason', [
    ('scene-clear.json', 0.1, 'valid', ''),
    ('scene-low-confidence.json', 0.1, 'unknown', 'low_confidence'),
    ('scene-stale.json', 2.0, 'unknown', 'stale_input'),
    ('scene-extra-command.json', 0.1, 'unknown', 'invalid_schema'),
])
def test_fixture_outcome(name, now_s, status, reason):
    scene = run(name, now_s)
    assert (scene['status'], scene['status_reason']) == (status, reason)
    assert SCHEMA_VALID(scene)


def SCHEMA_VALID(scene):  # noqa: N802
    from jsonschema import Draft202012Validator
    return Draft202012Validator(SCHEMA).is_valid(scene)


def test_unknown_is_canonical_and_keeps_stamp_frame():
    scene = run('scene-stale.json', 2.0)
    assert scene['stamp_s'] == 1.0 and scene['frame_id'] == 'base_link'
    assert scene['traffic_light'] == scene['direction_sign'] == 'unknown'
    assert scene['stop_line_distance_m'] is None and scene['turn_distance_m'] is None
    assert scene['obstacle_distance_m'] is None and scene['confidence'] == 0


def test_drive_field_never_survives():
    scene = run('scene-extra-command.json', 0.1)
    assert 'drive' not in scene


def test_stale_boundary_uses_same_clock():
    assert run('scene-clear.json', 0.25)['status'] == 'valid'
    assert run('scene-clear.json', 0.2501)['status_reason'] == 'stale_input'


def test_invalid_input_types():
    for raw in (None, [], 'text', {'version': 2}):
        scene = evaluate_scene(raw, SCHEMA, now_s=0.0, source='mock')
        assert scene['status_reason'] == 'invalid_schema'
        assert SCHEMA_VALID(scene)


def test_canonical_unknown_falls_back_on_bad_stamp():
    scene = canonical_unknown({'stamp_s': -1, 'frame_id': ''}, 'invalid_schema', 'mock')
    assert scene['stamp_s'] == 0.0 and scene['frame_id'] == 'base_link'


# ---------- ключ кэша ----------

BASE = {'image_sha256': 'a' * 64, 'prompt_sha256': 'b' * 64, 'model_id': 'qwen3.8-27b',
        'generation_config': {'temperature': 0.0, 'max_tokens': 256}}


def test_key_is_sha256_of_sorted_compact_json():
    import hashlib
    payload = {'generation_config': {'max_tokens': 256, 'temperature': 0.0},
               'image_sha256': 'a' * 64, 'model_id': 'qwen3.8-27b',
               'prompt_sha256': 'b' * 64, 'schema_version': 1}
    text = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    assert cache_key(**BASE) == hashlib.sha256(text.encode()).hexdigest()


@pytest.mark.parametrize('component,value', [
    ('image_sha256', 'c' * 64),
    ('prompt_sha256', 'd' * 64),
    ('model_id', 'qwen3.8-7b'),
    ('generation_config', {'temperature': 0.2, 'max_tokens': 256}),
])
def test_each_component_changes_key(component, value):
    changed = dict(BASE, **{component: value})
    assert cache_key(**changed) != cache_key(**BASE)


class CountingBackend:
    """Локальный backend: возвращает сырой fixture и считает вызовы."""

    def __init__(self, raw):
        self.raw, self.calls = raw, 0

    def __call__(self, image_sha256, prompt_text, model_id, generation_config):
        self.calls += 1
        return self.raw


def make_cache(tmp_path, raw):
    backend = CountingBackend(raw)
    return SceneCache(tmp_path / 'cache', backend), backend


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding='utf-8')
    return path


def test_miss_calls_backend_hit_does_not(tmp_path):
    cache, backend = make_cache(tmp_path, fixture('scene-clear.json'))
    prompt = write(tmp_path, 'prompt.txt', 'describe the road')
    _, hit1 = cache.get('a' * 64, prompt, 'm', {'t': 0})
    _, hit2 = cache.get('a' * 64, prompt, 'm', {'t': 0})
    assert (hit1, hit2, backend.calls) == (False, True, 1)


@pytest.mark.parametrize('change', ['image', 'prompt', 'model', 'config'])
def test_every_component_misses(tmp_path, change):
    cache, backend = make_cache(tmp_path, fixture('scene-clear.json'))
    prompt = write(tmp_path, 'p1.txt', 'describe the road')
    cache.get('a' * 64, prompt, 'm', {'t': 0})
    args = ['a' * 64, prompt, 'm', {'t': 0}]
    if change == 'image':
        args[0] = 'e' * 64
    elif change == 'prompt':
        args[1] = write(tmp_path, 'p2.txt', 'describe the road and signs')
    elif change == 'model':
        args[2] = 'other'
    else:
        args[3] = {'t': 1}
    _, hit = cache.get(*args)
    assert hit is False and backend.calls == 2


def test_cache_hit_is_rechecked_for_age(tmp_path):
    cache, _ = make_cache(tmp_path, fixture('scene-clear.json'))
    prompt = write(tmp_path, 'prompt.txt', 'x')
    cache.get('a' * 64, prompt, 'm', {})
    raw, hit = cache.get('a' * 64, prompt, 'm', {})
    assert hit
    assert evaluate_scene(raw, SCHEMA, now_s=2.0, source='cache')['status_reason'] == \
        'stale_input'


def test_miss_without_backend_is_explicit_error(tmp_path):
    cache = SceneCache(tmp_path / 'cache', backend=None)
    prompt = write(tmp_path, 'prompt.txt', 'x')
    with pytest.raises(RuntimeError, match='backend'):
        cache.get('a' * 64, prompt, 'm', {})


def test_prompt_hash_reads_actual_file(tmp_path):
    p = write(tmp_path, 'p.txt', 'abc')
    assert sha256_file(p) == \
        'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
