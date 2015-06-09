from setuptools import setup


setup(
    name="aiogremlin",
    version="0.0.9",
    url="",
    license="MIT",
    author="davebshow",
    author_email="davebshow@gmail.com",
    description="Python 3 driver for TP3 Gremlin Server built on Asyncio and aiohttp",
    long_description=open("README.txt").read(),
    packages=["aiogremlin", "tests"],
    install_requires=[
        "aiohttp==0.16.3"
    ],
    test_suite="tests",
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
