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
    tests.test_linchpin_wrapper

    Unit tests for testing carbon LinchpinWrapperProvisioner class.

    :copyright: (c) 2018 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import json
import pytest
import mock
from carbon.resources import Host
from carbon.core import CarbonProvisioner
from carbon.exceptions import CarbonProvisionerError
from carbon.provisioners import LinchpinWrapperProvisioner
from linchpin import LinchpinAPI


def os_params():
    return dict(
        role='client',
        provider=dict(
            name='openstack',
            credential='openstack',
            image='image',
            flavor='small',
            networks=['network'],
            keypair='key',
            floating_ip_pool='pool',
            tx_id = 1
        )
    )


def beaker_params():
    return dict(
        role='client',
        provider=dict(
            name='beaker',
            credential='beaker-creds',
            arch='x86_64',
            distro='RHEL-7.5',
            variant='Server',
            whiteboard='carbon beaker resource examples',
            tx_id = 1
        )
    )


def libvirt_params():
    return dict(
        role='client',
        provider=dict(
            name='libvirt',
            credential='libvirt-creds',
            role='libvirt_node',
            vcpus=2,
            memory=1024,
            uri='qemu:///system',
            image_src='http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2',
            ssh_key='carbon',
            libvirt_become='no',
            libvirt_image_path='~/libvirt/images/',
            libvirt_user='test',
            tx_id=1,
            networks=[dict(name='test_libvirt_net')]
        )
    )

def aws_params():
    return dict(
        role='client',
        provider=dict(
            name='aws',
            credential='aws-creds',
            role='aws_ec2',
            flavor='t2.nano',
            image='ami-0200c593f80612761',
            region='us-east-2',
            tx_id=1
        )
    )


@pytest.fixture(params=['os', 'beaker', 'libvirt', 'aws'])
def host(request, config):
    return Host(
        name='host01',
        config=config,
        provisioner='linchpin-wrapper',
        parameters=copy.deepcopy(eval('%s_params()' % request.param))
    )


@pytest.fixture
def linchpin_wrapper(host):
    return LinchpinWrapperProvisioner(host)


class TestLinchpinWrapperProvisioner(object):
    def do_action(*args, **kwargs):
        pinfile = args[1]
        resource = pinfile['carbon']['topology']['resource_groups'][0]
        cloud = resource['resource_group_type']
        if kwargs['action'] == 'up':
            sample_file = '../assets/linchpin_%s_results.json' % cloud
            with open(sample_file) as sample:
                results = json.load(sample)
            return (0, [results])
        elif kwargs['action'] == 'destroy':
            return True

    def up_failed(self, *args, **kwargs):
        return (1, {})

    def get_run_data(*args, **kwargs):
        return args[1]


    @staticmethod
    def test_linchpin_constructor(linchpin_wrapper):
        assert isinstance(linchpin_wrapper, LinchpinWrapperProvisioner)

    @staticmethod
    @mock.patch.object(LinchpinAPI, 'do_action', do_action)
    def test_linchpin_delete(linchpin_wrapper):
        linchpin_wrapper.delete()

    @staticmethod
    @mock.patch.object(LinchpinAPI, 'do_action', up_failed)
    def test_linchpin_failed_os_create(linchpin_wrapper):
        with pytest.raises(CarbonProvisionerError):
            linchpin_wrapper.create()

    @staticmethod
    @mock.patch.object(LinchpinAPI, 'do_action', do_action)
    @mock.patch.object(LinchpinAPI, 'get_run_data', get_run_data)
    def test_linchpin_wrapper_create(linchpin_wrapper):
        linchpin_wrapper.create()
        assert getattr(linchpin_wrapper.host, 'ip_address') == "10.0.58.5"
