from setuptools import setup


setup(
    name='aiogremlin',
    version='3.2.4',
    url='',
    license='MIT',
    author='davebshow',
    author_email='davebshow@gmail.com',
    description='Async Gremlin-Python',
    long_description=open('README.txt').read(),
    packages=['aiogremlin', 'aiogremlin.driver', 'aiogremlin.driver.aiohttp',
              'aiogremlin.gremlin_python', 'aiogremlin.gremlin_python.driver',
              'aiogremlin.gremlin_python.process',
              'aiogremlin.gremlin_python.structure',
              'aiogremlin.gremlin_python.structure.io',
              'aiogremlin.remote'],
    install_requires=[
        'aiohttp==1.3.3',
        'PyYAML==3.12'
    ],
    test_suite='tests',
    setup_requires=['pytest-runner'],
    tests_require=['pytest-asyncio', 'pytest', 'mock'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only'
    ]
)
