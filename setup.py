#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Yeolar
#

from setuptools import setup, find_packages


setup(
    name='bunder',
    version='0.1',
    description='A pack and deploy tool.',
    long_description=open('README.md').read(),
    license='Apache 2.0',
    author='Yeolar',
    author_email='yeolar@gmail.com',
    url='http://www.rddoc.com',
    packages=find_packages(),
    install_requires=[
    ],
    entry_points={
        'console_scripts': [
            'bunder = bunder:main',
        ]
    },
)
