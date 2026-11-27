from glob import glob

from setuptools import find_packages, setup

package_name = 'scene_adapter'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='LessVegetables',
    maintainer_email='57289239+LessVegetables@users.noreply.github.com',
    description='Адаптер VLM: mock/cache/live -> SceneDescription v1',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'scene_adapter = scene_adapter.node:main',
            'check_fixtures = scene_adapter.check_fixtures:main',
        ],
    },
)
