from setuptools import find_packages, setup

package_name = 'subteam2_driving'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            ['launch/driving.launch.py']),
        ('share/' + package_name + '/config',
            ['config/driving_params.yaml']),
        ('share/' + package_name + '/config',
            ['config/driving_params.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yahboom',
    maintainer_email='your_email@example.com',
    description='Driving package for Subteam 2',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'drive_controller = subteam2_driving.drive_controller:main',
            'test_pattern = subteam2_driving.test_pattern:main',
            'stop_reset_service = subteam2_driving.stop_reset_service:main',
        ],
    },
)
