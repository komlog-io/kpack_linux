from setuptools import setup

setup(
    name = 'kpack_linux',
    license = 'Apache Software License',
    packages = ['kpack_linux'],
    version = '0.1',
    entry_points = {
        'komlogd.package': 'load = kpack_linux.load'
    }
)

