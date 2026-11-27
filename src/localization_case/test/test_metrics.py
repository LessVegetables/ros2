"""ПР08: окно измерения, шаги 0,1 с, медиана ковариации, сборка отчёта."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load('measure_localization')
r = load('make_localization_report')


def test_window_is_relative_to_first_clock():
    t0 = 42.0
    assert not m.in_window(51.99, t0)
    assert m.in_window(52.0, t0)
    assert m.in_window(71.99, t0)
    assert not m.in_window(72.0, t0)


def test_two_hundred_slots_in_window():
    t0 = 112.64
    slots = {m.slot_index(t0 + 10 + k * 0.1 + 0.001, t0) for k in range(200)}
    assert slots == set(range(200))


def test_xy_covariance_uses_elements_0_and_7():
    cov = [0.0] * 36
    cov[0], cov[7], cov[35] = 0.1, 0.05, 9.0
    assert m.xy_covariance(cov) == pytest.approx(0.15)


def test_summarize_availability_and_median():
    s = m.summarize(195, 200, [0.3, 0.1, 0.2])
    assert s['tf_availability'] == pytest.approx(0.975)
    assert s['median_xy_covariance_m2'] == pytest.approx(0.2)
    assert s['amcl_pose_samples'] == 3


def test_summarize_defect_all_failed():
    s = m.summarize(0, 200, [])
    assert s['tf_availability'] == 0.0 and s['median_xy_covariance_m2'] is None


def test_report_matches_schema_shape(tmp_path):
    (tmp_path / 'map.yaml').write_text('image: map.pgm\n')
    (tmp_path / 'map.pgm').write_bytes(b'P5\n1 1\n255\n\x00')
    bag = tmp_path / 'bag'
    bag.mkdir()
    (bag / 'metadata.yaml').write_text(
        'rosbag2_bagfile_information:\n  duration:\n    nanoseconds: 36343000000\n')
    metrics = {'warmup_s': 10.0, 'duration_s': 20.0, 'tf_queries_total': 200,
               'tf_queries_successful': 200, 'tf_availability': 1.0,
               'amcl_pose_samples': 40, 'median_xy_covariance_m2': 0.01}
    report = r.build(metrics, tmp_path / 'map.yaml', tmp_path / 'map.pgm', bag, 'x')
    assert report['recording']['duration_s'] == pytest.approx(36.343)
    assert len(report['map_sha256']['map.pgm']) == 64
    assert set(report) == {'schema_version', 'map_sha256', 'recording', 'initial_pose',
                           'evaluation', 'defect'}
    json.dumps(report)
