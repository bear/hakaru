#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from hakaru import __version__

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='hakaru',
    version=__version__,
    description='Monitoring and Alerts',
    long_description=readme,
    author='Mike Taylor',
    author_email='bear@bear.im',
    url='https://github.com/bear/hakaru',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)