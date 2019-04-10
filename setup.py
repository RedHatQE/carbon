# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Interoperability framework (codename 'carbon').
"""
import os
import re

from setuptools import setup, find_packages

ROOT = os.path.dirname(__file__)
VERSION_RE = re.compile(r'''__version__ = ['"]([a-zA-Z0-9.]+)['"]''')


def get_version():
    init = open(os.path.join(ROOT, 'carbon', '__init__.py')).read()
    return VERSION_RE.search(init).group(1)


setup(
    name='carbon',
    version=get_version(),
    license='GPLv3',
    author='Red Hat Inc.',
    description='A framework to test product interoperability',
    long_description=__doc__,
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'ansible>=2.5.0',
        'apache-libcloud==2.2.0',
        'blaster>=0.1.8',
        'Click>=6.7',
        'Jinja2>=2.10',
        'pykwalify>=1.6.0',
        'python-cachetclient',
        'ruamel.yaml>=0.15.64'
    ],
    extras_require={
        'linchpin': ['linchpin==1.7.3'],
        'linchpin-bkr': ['linchpin[beaker]==1.7.3']
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GPLv3 License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': ['carbon=carbon.cli:carbon']
    }
)
