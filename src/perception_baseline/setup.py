from glob import glob

from setuptools import find_packages, setup

package_name = 'perception_baseline'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'README.md']),
        ('share/' + package_name + '/config', glob('config/*.json')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='LessVegetables',
    maintainer_email='57289239+LessVegetables@users.noreply.github.com',
    description='Красный baseline-детектор, 2D/3D через ROS',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'perception_baseline = perception_baseline.node:main',
            'publish_pair = perception_baseline.publish_pair:main',
        ],
    },
)
