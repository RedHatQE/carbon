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
VERSION_RE = re.compile(r'''__version__ = ['"]([0-9.]+)['"]''')

dependencies = [
    'https://github.com/mkollaro/taskrunner/tarball/master#egg=taskrunner-0.3.0',
    'https://github.com/CentOS-PaaS-SIG/linch-pin/develop#egg=linchpin'
]

requires = [
    'Flask',
    'Werkzeug',
    'Click',
    'taskrunner==0.3.0',
    'PyYAML',
    'pykwalify',
    'linchpin'
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
    dependency_links=dependencies,
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
