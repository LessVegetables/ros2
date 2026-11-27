"""ПР06: развёрнутый Xacro — связное ациклическое дерево с ожидаемыми связями."""

import math
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest

XACRO = Path(__file__).resolve().parents[1] / 'urdf' / 'vehicle.urdf.xacro'
SENSOR_XYZ = (0.28, 0.0, 0.38)   # из course kit models/course_ackermann/model.sdf


@pytest.fixture(scope='module')
def urdf_text() -> str:
    return subprocess.run(['xacro', str(XACRO)], check=True, capture_output=True,
                          text=True).stdout


@pytest.fixture(scope='module')
def robot(urdf_text: str) -> ET.Element:
    return ET.fromstring(urdf_text)


def joints(robot: ET.Element) -> dict:
    return {j.get('name'): j for j in robot.findall('joint')}


def parent_of(robot: ET.Element, child: str) -> str:
    for joint in robot.findall('joint'):
        if joint.find('child').get('link') == child:
            return joint.find('parent').get('link')
    raise AssertionError(f'{child} не является дочерним звеном ни одного joint')


def xyz(joint: ET.Element) -> tuple:
    return tuple(float(v) for v in joint.find('origin').get('xyz').split())


def test_single_root_base_link_connected_acyclic(robot: ET.Element) -> None:
    links = {link.get('name') for link in robot.findall('link')}
    children = [j.find('child').get('link') for j in robot.findall('joint')]
    assert len(children) == len(set(children)), 'у звена больше одного родителя'
    roots = links - set(children)
    assert roots == {'base_link'}
    for link in links - {'base_link'}:        # от каждого звена дойти до корня без цикла
        seen, node = set(), link
        while node != 'base_link':
            assert node not in seen, f'цикл через {node}'
            seen.add(node)
            node = parent_of(robot, node)


@pytest.mark.parametrize('sensor', ['camera_link', 'lidar_link', 'imu_link'])
def test_sensor_parent_is_base_link(robot: ET.Element, sensor: str) -> None:
    assert parent_of(robot, sensor) == 'base_link'


def test_lidar_expected_parent_and_offset(robot: ET.Element) -> None:
    joint = joints(robot)['lidar_joint']
    assert joint.get('type') == 'fixed'
    assert joint.find('parent').get('link') == 'base_link'
    assert xyz(joint) == pytest.approx(SENSOR_XYZ)


def test_wheel_positions_follow_parameters(robot: ET.Element) -> None:
    j = joints(robot)
    assert xyz(j['front_left_steering_joint']) == pytest.approx((0.40, 0.31, 0.0))
    assert xyz(j['front_right_steering_joint']) == pytest.approx((0.40, -0.31, 0.0))
    assert xyz(j['rear_left_wheel_joint']) == pytest.approx((-0.40, 0.31, 0.0))
    assert xyz(j['rear_right_wheel_joint']) == pytest.approx((-0.40, -0.31, 0.0))
    for name in ('front_left_wheel_joint', 'rear_right_wheel_joint'):
        assert j[name].get('type') == 'continuous'
        assert j[name].find('axis').get('xyz') == '0 1 0'


def test_visual_and_collision_present(robot: ET.Element) -> None:
    for name in ('base_link', 'front_left_wheel', 'lidar_link', 'camera_link'):
        link = robot.find(f"link[@name='{name}']")
        assert link.find('visual') is not None and link.find('collision') is not None


def test_inertials_physically_valid(robot: ET.Element) -> None:
    for link in robot.findall('link'):
        inertial = link.find('inertial')
        if inertial is None:
            continue
        mass = float(inertial.find('mass').get('value'))
        i = inertial.find('inertia')
        ixx, iyy, izz = (float(i.get(k)) for k in ('ixx', 'iyy', 'izz'))
        assert mass > 0 and min(ixx, iyy, izz) > 0, link.get('name')
        assert ixx + iyy >= izz and iyy + izz >= ixx and ixx + izz >= iyy, link.get('name')
        assert all(math.isfinite(v) for v in (mass, ixx, iyy, izz))


@pytest.mark.skipif(shutil.which('check_urdf') is None, reason='check_urdf не найден')
def test_check_urdf_accepts_model(urdf_text: str, tmp_path: Path) -> None:
    path = tmp_path / 'vehicle.urdf'
    path.write_text(urdf_text, encoding='utf-8')
    result = subprocess.run(['check_urdf', str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'root Link: base_link' in result.stdout
