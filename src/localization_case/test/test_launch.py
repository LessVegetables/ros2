"""ПР08: launch объявляет аргументы и запускает три ноды с именами из YAML."""

import importlib.util
from pathlib import Path

from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
import yaml

PKG = Path(__file__).resolve().parents[1]


def load():
    spec = importlib.util.spec_from_file_location('loc', PKG / 'launch' / 'localization.launch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_launch_description()


def test_arguments():
    names = {a.name for a in load().entities if isinstance(a, DeclareLaunchArgument)}
    assert {'params_file', 'map'} <= names


def test_three_nodes_match_yaml_keys():
    nodes = [a for a in load().entities if isinstance(a, Node)]
    assert len(nodes) == 3
    params = yaml.safe_load((PKG / 'config' / 'amcl.yaml').read_text())
    assert set(params) == {'amcl', 'map_server', 'lifecycle_manager_localization'}
    assert params['lifecycle_manager_localization']['ros__parameters']['node_names'] == [
        'map_server', 'amcl']


def test_profile_uses_base_link():
    params = yaml.safe_load((PKG / 'config' / 'amcl.yaml').read_text())
    assert params['amcl']['ros__parameters']['base_frame_id'] == 'base_link'
    assert params['amcl']['ros__parameters']['scan_topic'] == '/vehicle/scan'
