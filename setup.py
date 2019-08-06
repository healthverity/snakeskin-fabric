#!/usr/bin/env python
"""
    Setup.py for snakeskin
"""

import io
import os
from setuptools import setup
from snakeskin import __version__

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

with open('./requirements.txt') as reqs_txt:
    REQS = [line for line in reqs_txt]

setup(
    name='snakeskin',
    version=__version__,
    keywords=('Hyperledger Fabric', 'SDK'),
    description="An unofficial Python SDK for Hyperledger Fabric",
    long_description=io.open('README.md', encoding='utf-8').read(),
    author='HealthVerity',
    url='https://github.com/healthverity/snakeskin/',
    download_url='https://github.com/healthverity/snakeskin/',
    packages=['snakeskin'],
    platforms='any',
    install_requires=REQS,
    zip_safe=False,
    test_suite='test',
    include_package_data=True,
)
