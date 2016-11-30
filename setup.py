#!/usr/bin/env python

import os
import re
import sys

from codecs import open

from setuptools import setup
from setuptools.command.test import test as TestCommand


packages = [
    'libpth',
]

requires = [
    'requests',
]

with open('libpth/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

setup(
    name='libpth',
    version=version,
    description='Shared library for PTH projects.',
    long_description=readme,
    author='#pth-dev',
    packages=packages,
    package_data={'': ['LICENSE']},
    package_dir={'libpth': 'libpth'},
    include_package_data=True,
    install_requires=requires,
    license='GNU GPLv3',
    zip_safe=False,
)
