from setuptools import setup, find_packages

setup(
    name='unaceba',
    version='0.0.0',
    packages=find_packages(),
    install_requires=[],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/unaceba']),
        ('share/unaceba', ['package.xml']),
    ],
)
