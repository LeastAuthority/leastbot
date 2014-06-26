#! /usr/bin/env python

from setuptools import setup, find_packages


setup(
    name='leastbot',
    description='leastbot - Least Authority ircbot / webhook thingy.',
    url='https://github.com/nejucomo/leastbot',
    license='GPLv3',
    version='0.1.dev0',
    author='Nathan Wilcox',
    author_email='nathan@leastauthority.com',
    packages=find_packages(),
    install_requires=[
        'twisted >= 13.1',
        'Mock >= 1.0.1',
        ],
    test_suite='leastbot.tests',
    entry_points = {
        'console_scripts': [
            'leastbot = leastbot.main:main',
            ],
        },
    )
