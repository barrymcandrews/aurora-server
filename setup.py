from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='aurora_server',
    version='2.0',
    description='Controls RGB LED lights with a RESTful web API.',
    author='M. Barry McAndrews',
    author_email='bmcandrews@pitt.edu',
    ext_modules=cythonize(['aurora_server_flask.pyx']),
    requires=['numpy', 'Cython', 'flask']
)
