import pip
from setuptools import setup
from distutils.command.build_py import build_py as _build_py


class build_py(_build_py):
    """Don't install tornado when installing gremlinpython"""
    pip.main([
    'install',
    'git+https://git-wip-us.apache.org/repos/asf/tinkerpop.git@12aa2d2fe534fbd9540c9328725ab844e4bb1010#egg=gremlinpython&subdirectory=gremlin-python/src/main/jython',
    '--no-deps'])


setup(
    name='aiogremlin',
    version='3.2.5rc1',
    url='',
    license='Apache Software License',
    author='davebshow',
    author_email='davebshow@gmail.com',
    description='Async Gremlin-Python',
    long_description=open('README.txt').read(),
    packages=['aiogremlin',
              'aiogremlin.driver',
              'aiogremlin.driver.aiohttp',
              'aiogremlin.process',
              'aiogremlin..structure',
              'aiogremlin.remote'],
    cmdclass={'build_py': build_py},
    install_requires=[
        'aenum==1.4.5',  # required gremlinpython dep
        'aiohttp==1.3.3',
        'PyYAML==3.12',
        'six==1.10.0'  # required gremlinpython dep
    ],
    test_suite='tests',
    setup_requires=['pytest-runner'],
    tests_require=['pytest-asyncio', 'pytest', 'mock'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only'
    ]
)
