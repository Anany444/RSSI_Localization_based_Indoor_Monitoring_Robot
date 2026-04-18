from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'rssi'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pi',
    maintainer_email='pi@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
	    "data_collect = rssi.data_collect:main",
            "velocity_relay = rssi.velocity_relay:main",
            "data_zone_service = rssi.data_zone_serv:main",
            "broadcaster = rssi.broadcaster_qos:main",
            "rssi_logger = rssi.rssi_logger:main",

        ],
    },
)
