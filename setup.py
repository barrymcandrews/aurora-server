#!/usr/bin/env python3.7

from setuptools import setup, find_packages
from Cython.Build import cythonize

install_requires = [
    'numpy',
    'Cython',
    'uvloop',
    'aiofiles',
    'sanic',
    'sanic_openapi',
    'wiringpi',
    'setproctitle',
    'pyalsaaudio'
]

setup(
    name='aurora_server',
    version='2.1',
    description='Controls RGB LED lights with a RESTful web API.',
    author='M. Barry McAndrews',
    author_email='bmcandrews@pitt.edu',
    ext_modules=cythonize(['aurora/visualizer/*.pyx', 'aurora/hardware.pyx']),
    requires=install_requires,
    packages=find_packages(),
    data_files=[
        ('/etc', ['config/aurora.conf']),
        ('/etc/systemd/system', ['config/aurora.service'])
    ],
    entry_points={
        'console_scripts': [
            'aurora = aurora.__main__:main'
        ]
    }
)
