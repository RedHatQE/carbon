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
    tests.test_linchpin_wrapper_plugin

    Unit tests for testing carbon LinchpinWrapperProvisionerPlugin class.

    :copyright: (c) 2018 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import copy
import json
import pytest
import mock
from carbon.resources import Asset
from carbon.core import CarbonProvisioner
from carbon.exceptions import CarbonProvisionerError
from carbon.provisioners.ext import LinchpinWrapperProvisionerPlugin
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
            tx_id=1,
            count=1
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
            tx_id=1
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


@pytest.fixture(params=['os', 'aws', 'beaker', 'libvirt'])
def asset(request, config):
    return Asset(
        name='host01',
        config=config,
        provisioner='linchpin-wrapper',
        parameters=copy.deepcopy(eval('%s_params()' % request.param))
    )


@pytest.fixture
def linchpin_wrapper_plugin(asset):
    profile = asset.profile()
    profile.update(provider_credentials=getattr(getattr(
        asset, 'provider'), 'credentials'), config_params={})
    return LinchpinWrapperProvisionerPlugin(profile)


class TestLinchpinWrapperProvisionerPlugin(object):
    def do_action(*args, **kwargs):
        pinfile = args[1]
        resource = pinfile['carbon']['topology']['resource_groups'][0]
        cloud = resource['resource_group_type']
        if kwargs['action'] == 'up':
            sample_file = '../assets/linchpin_%s_count_results.json' % cloud
            with open(sample_file) as sample:
                results = json.load(sample)
            return 0, [results]
        elif kwargs['action'] == 'destroy':
            return 0, None

    def up_failed(self, *args, **kwargs):
        return (1, {})

    def get_run_data(*args, **kwargs):
        return args[1]

    def destroy_failed(self, *args, **kwargs):
        return (1, {})

    @staticmethod
    def test_linchpin_constructor(linchpin_wrapper_plugin):
        assert isinstance(linchpin_wrapper_plugin, LinchpinWrapperProvisionerPlugin)

    @staticmethod
    @mock.patch.object(LinchpinAPI, 'do_action', do_action)
    def test_linchpin_delete(linchpin_wrapper_plugin):
        linchpin_wrapper_plugin.delete()

    @staticmethod
    @mock.patch.object(LinchpinAPI, 'do_action', up_failed)
    def test_linchpin_failed_os_create(linchpin_wrapper_plugin):
        with pytest.raises(CarbonProvisionerError):
            res = linchpin_wrapper_plugin.create()

    @staticmethod
    @mock.patch.object(LinchpinAPI, 'do_action', destroy_failed)
    def test_linchpin_failed_os_destroy(linchpin_wrapper_plugin):
        with pytest.raises(CarbonProvisionerError):
            linchpin_wrapper_plugin.delete()

    @staticmethod
    @mock.patch.object(LinchpinAPI, 'do_action', do_action)
    @mock.patch.object(LinchpinAPI, 'get_run_data', get_run_data)
    def test_linchpin_wrapper_create(linchpin_wrapper_plugin):
        res = linchpin_wrapper_plugin.create()
        assert (res[0]['ip'] == "10.0.151.56" or isinstance(res[0]['ip'],dict))
        assert (res[1]['ip'] == "10.0.150.117" or isinstance(res[1]['ip'],dict))

