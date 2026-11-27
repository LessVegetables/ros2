"""Проверить четыре fixture ПР10: сырой ответ по схеме и итог адаптера (без сети)."""

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from scene_adapter.core import evaluate_scene, load_schema

CASES = (
    ('scene-clear.json', 0.1),
    ('scene-low-confidence.json', 0.1),
    ('scene-stale.json', 2.0),
    ('scene-extra-command.json', 0.1),
)


def main() -> int:
    """Напечатать по строке на fixture и вернуть 0, если ожидания README совпали."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, default=Path('fixtures/vlm'))
    parser.add_argument('--schema', type=Path,
                        default=Path('contracts/scene-description-v1.schema.json'))
    parser.add_argument('--abstain-threshold', type=float, default=0.5)
    parser.add_argument('--max-age-s', type=float, default=0.25)
    args = parser.parse_args()
    schema = load_schema(args.schema)
    validator = Draft202012Validator(schema)
    expected = {'scene-clear.json': ('valid', ''),
                'scene-low-confidence.json': ('unknown', 'low_confidence'),
                'scene-stale.json': ('unknown', 'stale_input'),
                'scene-extra-command.json': ('unknown', 'invalid_schema')}
    ok = True
    print(f'abstain_threshold={args.abstain_threshold} max_age_s={args.max_age_s}')
    for name, now_s in CASES:
        raw = json.loads((args.fixtures / name).read_text(encoding='utf-8'))
        errors = sorted(e.message for e in validator.iter_errors(raw))
        scene = evaluate_scene(raw, schema, now_s=now_s, source='mock',
                               abstain_threshold=args.abstain_threshold,
                               max_age_s=args.max_age_s)
        result = (scene['status'], scene['status_reason'])
        out_valid = validator.is_valid(scene)
        match = result == expected[name] and out_valid
        ok &= match
        print(f'{name}: now_s={now_s} raw_schema={"ok" if not errors else errors} '
              f'-> status={result[0]} reason={result[1]!r} output_schema_ok={out_valid} '
              f'{"OK" if match else "MISMATCH"}')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
