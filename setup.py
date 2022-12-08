import os

from setuptools import setup, find_packages


def get_version(package_path):
    """Возвращает версию пакета без импорта"""
    _locals = {}
    with open(os.path.join(package_path, '_version.py')) as version_file:
        exec(version_file.read(), None, _locals)  # pylint: disable=exec-used
    return _locals["__version__"]


version = get_version('sources/agent')

setup(
    name='inotify_agent',
    version=version,
    author='Vitaliy Gluhih',
    author_email='vagluxix@gmail.com',
    description='Inotify agent',
    url='<no public>',

    packages=find_packages('sources'),
    package_dir={'': 'sources'},
    include_package_data=True,

    python_requires='>=3.8',
    install_requires=[
        'wheel>=0.37.0',
        'pykka>=3.0.2',
        'amqp>=5.0.1,<5.1',
        'paho-mqtt>=1.5.1,<1.6',
        'certifi>=2021.5.30',
        'watchdog>=2.1.6',
        'inotify'
    ],
    extras_require={
        'dev': [
            # Tests
            'pytest>=5.4.1,<5.5',
            'pylint>=2.6.0,<2.7',

            # Build
            'invoke>=1.4.1,<1.5',
        ]
    },
    entry_points='''
        [console_scripts]
        
    ''',
)
