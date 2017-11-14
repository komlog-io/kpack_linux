from setuptools import setup

setup(
    name = 'kpack_linux',
    license = 'Apache Software License',
    packages = ['kpack_linux'],
    version = '0.2',
    test_suite = 'kpack_linux',
    entry_points = {
        'komlogd.package': 'load = kpack_linux.load'
    }
)

