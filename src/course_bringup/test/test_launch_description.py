"""Структура patrol.launch.py: аргументы, namespace, условие записи."""

import importlib.util
from pathlib import Path

from launch import LaunchContext, LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
import pytest

LAUNCH = Path(__file__).resolve().parents[1] / 'launch' / 'patrol.launch.py'


def load() -> LaunchDescription:
    spec = importlib.util.spec_from_file_location('patrol_launch', LAUNCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_launch_description()


def test_declares_required_arguments():
    names = {a.name for a in load().entities if isinstance(a, DeclareLaunchArgument)}
    assert {'namespace', 'record', 'bag_dir', 'subscriber_reliability'} <= names


def test_defaults():
    args = {a.name: a for a in load().entities if isinstance(a, DeclareLaunchArgument)}
    assert args['record'].default_value[0].text == 'false'
    assert args['namespace'].default_value[0].text == 'robot_a'
    assert args['subscriber_reliability'].choices == ['reliable', 'best_effort']


@pytest.mark.parametrize('value,expected', [('true', True), ('false', False)])
def test_recorder_runs_only_when_record_true(value, expected):
    recorder = [a for a in load().entities if type(a) is ExecuteProcess]
    assert len(recorder) == 1
    condition = recorder[0].condition
    assert isinstance(condition, IfCondition)
    context = LaunchContext()
    context.launch_configurations['record'] = value
    assert condition.evaluate(context) is expected
