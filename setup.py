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

requires = [
    'pbr>=3.1.1',
    'Flask>=0.12.2',
    'Werkzeug>=0.11.15',
    'Click>=6.7',
    'PyYAML>=3.12',
    'pykwalify>=1.6.0',
    'apache-libcloud==2.2.0',
    'ansible>=2.3.2.0',
    'blinker==1.4',
    'blaster>=0.1.4'
]


def get_version():
    init = open(os.path.join(ROOT, 'src', 'carbon', '__init__.py')).read()
    return VERSION_RE.search(init).group(1)


setup(
    name='carbon',
    version=get_version(),
    url='https://mojo.redhat.com/groups/qe-product-interop-testing',
    license='GPLv3',
    author='PIT Team Red Hat',
    author_email='pit@redhat.com',
    description='A framework to test product interoperability',
    long_description=__doc__,
    package_dir={'': 'src'},
    packages=find_packages('src', exclude=['tests*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
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
    entry_points="""
        [console_scripts]
        carbon=carbon.cli:cli
    """
)
