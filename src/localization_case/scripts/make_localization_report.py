#!/usr/bin/env python3
"""ПР08: собрать localization.json из метрик измерителя, карты и metadata записи."""

import argparse
import hashlib
import json
from pathlib import Path
import re


def sha256(path: Path) -> str:
    """SHA-256 файла в hex."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bag_duration_s(metadata_yaml: Path) -> float:
    """Длительность записи (по /clock при --use-sim-time) из metadata.yaml, секунды."""
    text = metadata_yaml.read_text(encoding='utf-8')
    match = re.search(r'duration:\s*\n\s*nanoseconds:\s*(\d+)', text)
    if not match:
        raise ValueError(f'не найдена duration в {metadata_yaml}')
    return int(match.group(1)) / 1e9


def build(metrics: dict, map_yaml: Path, map_pgm: Path, bag: Path, symptom: str) -> dict:
    """Структура по localization-result-v1.schema.json."""
    return {
        'schema_version': 1,
        'map_sha256': {'map.yaml': sha256(map_yaml), 'map.pgm': sha256(map_pgm)},
        'recording': {'path': str(bag), 'duration_s': round(bag_duration_s(bag / 'metadata.yaml'), 3)},
        'initial_pose': {'x_m': 0.0, 'y_m': 0.0, 'yaw_rad': 0.0},
        'evaluation': {
            'warmup_s': metrics['warmup_s'],
            'duration_s': metrics['duration_s'],
            'tf_queries_total': metrics['tf_queries_total'],
            'tf_queries_successful': metrics['tf_queries_successful'],
            'tf_availability': metrics['tf_availability'],
            'amcl_pose_samples': metrics['amcl_pose_samples'],
            'median_xy_covariance_m2': metrics['median_xy_covariance_m2'],
        },
        'defect': {
            'before_base_frame_id': 'chassis',
            'after_base_frame_id': 'base_link',
            'observed_symptom': symptom,
        },
    }


def main() -> int:
    """CLI: --metrics --map-yaml --map-pgm --bag --symptom --output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--map-yaml', type=Path, required=True)
    parser.add_argument('--map-pgm', type=Path, required=True)
    parser.add_argument('--bag', type=Path, required=True)
    parser.add_argument('--symptom', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    metrics = json.loads(args.metrics.read_text(encoding='utf-8'))
    report = build(metrics, args.map_yaml, args.map_pgm, args.bag, args.symptom)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n',
                           encoding='utf-8')
    print(json.dumps(report['evaluation'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
