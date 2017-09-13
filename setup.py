#!/usr/bin/env python3.6

from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='aurora_server',
    version='2.0',
    description='Controls RGB LED lights with a RESTful web API.',
    author='M. Barry McAndrews',
    author_email='bmcandrews@pitt.edu',
    ext_modules=cythonize(['aurora/visualizer/*.pyx', 'aurora/hardware.pyx']),
    requires=['numpy', 'Cython', 'flask', 'uvloop', 'aiofiles', 'sanic', 'wiringpi', 'setproctitle']
)
