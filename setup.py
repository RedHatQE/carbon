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
        "blaster==0.3.0",
        'Click>=6.7',
        'Jinja2>=2.10',
        'pykwalify>=1.6.0',
        'python-cachetclient',
        'ruamel.yaml>=0.15.64',
        'paramiko>=2.4.2',
        'requests>=2.20.1',
        'urllib3==1.24.3'
    ],
    extras_require={'linchpin-wrapper': ['carbon_linchpin_plugin@git+https://gitlab.cee.redhat.com/ccit/carbon/plugins/carbon_linchpin_plugin.git@1.0.1#egg=carbon_linchpin_plugin']},
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
        'console_scripts': ['carbon=carbon.cli:carbon'],
        'provider_plugins': [
            'aws_provider = carbon.providers:AwsProvider',
            'beaker_provider = carbon.providers:BeakerProvider',
            'libvirt_provider = carbon.providers:LibvirtProvider',
            'openstack_provider = carbon.providers:OpenstackProvider'
             ],
        'provisioner_plugins': [
            'beaker_client = carbon.provisioners.ext:BeakerClientProvisionerPlugin',
            'openstack_libcloud = carbon.provisioners.ext:OpenstackLibCloudProvisionerPlugin'
        ],
        'orchestrator_plugins': [
            'ansible = carbon.orchestrators:AnsibleOrchestrator'
        ],
        'executor_plugins': [
            'runner = carbon.executors:RunnerExecutor'
        ],
        'notification_plugins': [
            'email-notifier = carbon.notifiers.ext:EmailNotificationPlugin'
        ]

    }
)
