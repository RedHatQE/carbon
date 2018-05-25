# -*- coding: utf-8 -*-
"""
Carbon
------

Carbon is a framework that cares about product interoperability quality.

Links
`````

* `website <https://mojo.redhat.com/groups/qe-product-interop-testing>`_

"""
import os
import re

from setuptools import setup, find_packages

ROOT = os.path.dirname(__file__)
VERSION_RE = re.compile(r'''__version__ = ['"]([a-zA-Z0-9.]+)['"]''')


def get_version():
    init = open(os.path.join(ROOT, 'carbon', '__init__.py')).read()
    return VERSION_RE.search(init).group(1)


def get_requirements():
    with open(os.path.join(ROOT, 'requirements.txt')) as f:
        return f.read()


setup(
    name='carbon',
    version=get_version(),
    url='https://mojo.redhat.com/groups/qe-product-interop-testing',
    license='GPLv3',
    author='PIT Team Red Hat',
    description='A framework to test product interoperability',
    long_description=__doc__,
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=get_requirements(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: GPLv3 License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': ['carbon=carbon.cli:cli']
    }
)
