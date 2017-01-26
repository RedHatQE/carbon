# -*- coding: utf-8 -*-
"""
Carbon
------

Carbon is a framework that cares about product interoperability quality.

Links
`````

* `website <https://mojo.redhat.com/groups/qe-product-interop-testing>`_

"""
import re
import ast
from setuptools import setup, find_packages


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('src/carbon/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='carbon',
    version=version,
    url='https://mojo.redhat.com/groups/qe-product-interop-testing',
    license='GPLv3',
    author='PIT Team at Red Hat',
    author_email='pit@redhat.com',
    description='A framework to test product interoperability',
    long_description=__doc__,
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Werkzeug',
        'Click',
        'taskrunner',
        'PyYAML'
    ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPLv3 License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Quality Assurance'
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points="""
        [console_scripts]
        carbon=carbon.cli:cli
    """
)
