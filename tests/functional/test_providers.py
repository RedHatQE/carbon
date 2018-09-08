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
    tests.test_providers

    Unit tests for testing carbon provider classes.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from carbon.exceptions import OpenstackProviderError
from carbon.providers import DigitalOceanProvider, RackspaceProvider, \
    StaticProvider, OpenshiftProvider, OpenstackProvider, AwsProvider, \
    BeakerProvider


@pytest.fixture(scope='class')
def provider_static():
    return StaticProvider()


@pytest.fixture(scope='class')
def rackspace_provider():
    return RackspaceProvider()


@pytest.fixture(scope='class')
def digitalocean_provider():
    return DigitalOceanProvider()


@pytest.fixture(scope='class')
def openshift_provider():
    return OpenshiftProvider()


@pytest.fixture(scope='class')
def openstack_provider():
    return OpenstackProvider()


@pytest.fixture(scope='class')
def aws_provider():
    return AwsProvider()


@pytest.fixture(scope='class')
def beaker_provider():
    return BeakerProvider()


class TestStaticProvider(object):
    @staticmethod
    def test_constructor(provider_static):
        assert isinstance(provider_static, StaticProvider)

    @staticmethod
    def test_validate_hostname(provider_static):
        assert provider_static.validate_hostname('host01')
        assert provider_static.validate_hostname(None)

    @staticmethod
    def test_validate_ip_address(provider_static):
        assert provider_static.validate_ip_address('127.0.0.1') == True

    @staticmethod
    def test_validate_name(provider_static):
        assert provider_static.validate_name(None) is False
        assert provider_static.validate_name('host01')
        assert provider_static.validate_name(True) is False


class TestRackspaceProvider(object):
    @staticmethod
    def test_constructor(rackspace_provider):
        assert isinstance(rackspace_provider, RackspaceProvider)


class TestDigitalOceanProvider(object):
    @staticmethod
    def test_constructor(digitalocean_provider):
        assert isinstance(digitalocean_provider, DigitalOceanProvider)


class TestOpenShiftProvider(object):
    @staticmethod
    def test_constructor(openshift_provider):
        assert isinstance(openshift_provider, OpenshiftProvider)

    @staticmethod
    def test_validate_name(openshift_provider):
        assert openshift_provider.validate_name(None) is False
        assert openshift_provider.validate_name(True) is False
        assert openshift_provider.validate_name('s2i')

    @staticmethod
    def test_validate_git(openshift_provider):
        assert openshift_provider.validate_git(None)
        assert openshift_provider.validate_git(True) is False
        assert openshift_provider.validate_git('https://github.com')

    @staticmethod
    def test_validate_image(openshift_provider):
        assert openshift_provider.validate_image(None)
        assert openshift_provider.validate_image('image')

    @staticmethod
    def test_validate_template(openshift_provider):
        assert openshift_provider.validate_template(None)
        assert openshift_provider.validate_template('template')

    @staticmethod
    def test_validate_custom_template(openshift_provider):
        assert openshift_provider.validate_custom_template(None)
        assert openshift_provider.validate_custom_template('template')

    @staticmethod
    def test_validate_env_vars(openshift_provider):
        assert openshift_provider.validate_env_vars(None)
        assert openshift_provider.validate_env_vars({'var_01': 'val_01'})

    @staticmethod
    def test_validate_build_timeout(openshift_provider):
        assert openshift_provider.validate_build_timeout(None)
        assert openshift_provider.validate_build_timeout(10)
        assert openshift_provider.validate_build_timeout(3.14) is False

    @staticmethod
    def test_validate_labels(openshift_provider):
        assert openshift_provider.validate_labels(None)
        assert openshift_provider.validate_labels('label') is False
        assert openshift_provider.validate_labels(['label']) is False
        assert openshift_provider.validate_labels([{'label1': 'value1'}])
        assert not openshift_provider.validate_labels([{'a': 'b', 'c': 'd'}])

    @staticmethod
    def test_validate_routes(openshift_provider):
        assert openshift_provider.validate_routes('route')

    @staticmethod
    def test_validate_custom_templates(openshift_provider):
        assert openshift_provider.validate_custom_templates('templates')

    @staticmethod
    def test_validate_app_names(openshift_provider):
        assert openshift_provider.validate_app_name('app')


class TestOpenStackProvider(object):
    @staticmethod
    def test_constructor(openstack_provider):
        assert isinstance(openstack_provider, OpenstackProvider)

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'size_lookup')
    def test_validate_flavor(mock_func, openstack_provider):
        assert openstack_provider.validate_flavor(None) is False
        assert openstack_provider.validate_flavor(['small']) is False
        mock_func.return_value = True
        assert openstack_provider.validate_flavor('small')
        mock_func.side_effect = OpenstackProviderError('invalid falvor')
        assert openstack_provider.validate_flavor('small') is False

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'image_lookup')
    def test_validate_image(mock_func, openstack_provider):
        assert openstack_provider.validate_image(None) is False
        assert openstack_provider.validate_image(['image']) is False
        mock_func.return_value = True
        assert openstack_provider.validate_image('image-01')
        mock_func.side_effect = OpenstackProviderError('invalid image')
        assert openstack_provider.validate_image('image-01') is False

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'network_lookup')
    def test_validate_networks(mock_func, openstack_provider):
        assert openstack_provider.validate_networks(None) is False
        assert openstack_provider.validate_networks('network') is False
        mock_func.return_value = True
        assert openstack_provider.validate_networks(['network-01'])
        mock_func.side_effect = OpenstackProviderError('invalid network')
        assert openstack_provider.validate_networks(['network-01']) is False

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'floating_ip_pool_lookup')
    def test_validate_floating_ip_pool(mock_func, openstack_provider):
        assert openstack_provider.validate_floating_ip_pool(None)
        assert openstack_provider.validate_floating_ip_pool(['a']) is False
        mock_func.return_value = True
        assert openstack_provider.validate_floating_ip_pool('127.0.0.1')
        mock_func.side_effect = OpenstackProviderError('invalid fip')
        assert not openstack_provider.validate_floating_ip_pool('127.0.0.1')

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'key_pair_lookup')
    def test_validate_key_pair(mock_func, openstack_provider):
        assert openstack_provider.validate_keypair(None) is False
        assert openstack_provider.validate_keypair(['a']) is False
        mock_func.return_value = True
        assert openstack_provider.validate_keypair('a')
        mock_func.side_effect = OpenstackProviderError('invalid key pair')
        assert openstack_provider.validate_keypair('a') is False

    @staticmethod
    def test_validate_admin_pass(openstack_provider):
        assert openstack_provider.validate_admin_pass('password')

    @staticmethod
    def test_validate_description(openstack_provider):
        assert openstack_provider.validate_description('description')

    @staticmethod
    def test_validate_files(openstack_provider):
        assert openstack_provider.validate_files('files')

    @staticmethod
    def test_validate_node_id(openstack_provider):
        assert openstack_provider.validate_node_id('node')

    @staticmethod
    def test_validate_ip_address(openstack_provider):
        assert openstack_provider.validate_ip_address('127.0.0.1')

    @staticmethod
    def test_validate_security_groups(openstack_provider):
        assert openstack_provider.validate_security_groups('default')

    @staticmethod
    def test_validate_name(openstack_provider):
        assert openstack_provider.validate_name(None) is False
        assert openstack_provider.validate_name(['name']) is False
        assert openstack_provider.validate_name('name')

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'driver')
    def test_key_pair_lookup(mock_func, openstack_provider):
        mock_func.list_key_pairs = mock.MagicMock()
        key_pair = mock.MagicMock()
        key_pair.name = 'default'
        mock_func.list_key_pairs.return_value = [key_pair]
        assert openstack_provider.key_pair_lookup('default').name == 'default'

        with pytest.raises(OpenstackProviderError) as ex:
            key_pair.name = 'custom'
            openstack_provider.key_pair_lookup('default')
        assert 'Keypair default not found!' in ex.value.args

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'driver')
    def test_float_ip_pool_lookup(mock_func, openstack_provider):
        mock_func.ex_list_floating_ip_pools = mock.MagicMock()
        fip = mock.MagicMock()
        fip.name = '127.0.0.1'
        mock_func.ex_list_floating_ip_pools.return_value = [fip]
        assert openstack_provider.floating_ip_pool_lookup('127.0.0.1')

        with pytest.raises(OpenstackProviderError) as ex:
            fip.name = '0.0.0.0'
            openstack_provider.floating_ip_pool_lookup('127.0.0.1')
        assert 'FIP 127.0.0.1 not found!' in ex.value.args

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'driver')
    def test_node_lookup(mock_func, openstack_provider):
        mock_func.list_nodes = mock.MagicMock()
        node = mock.MagicMock()
        node.name = 'node01'
        mock_func.list_nodes.return_value = [node]
        assert openstack_provider.node_lookup('node01')

        with pytest.raises(OpenstackProviderError) as ex:
            node.name = 'node02'
            openstack_provider.node_lookup('node01')
        assert 'Node node01 not found!' in ex.value.args

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'driver')
    def test_network_lookup(mock_func, openstack_provider):
        mock_func.ex_list_networks = mock.MagicMock()
        network = mock.MagicMock()
        network.name = 'net1'
        mock_func.ex_list_networks.return_value = [network]
        assert openstack_provider.network_lookup('net1')
        assert openstack_provider.network_lookup(['net1'])

        with pytest.raises(OpenstackProviderError) as ex:
            network.name = 'net2'
            assert openstack_provider.network_lookup('net1')
        assert 'Network(s) net1 not found!' in ex.value.args

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'driver')
    def test_image_lookup(mock_func, openstack_provider):
        mock_func.list_images = mock.MagicMock()
        image = mock.MagicMock()
        image.name = 'image01'
        image.id = '123'
        mock_func.list_images.return_value = [image]
        assert openstack_provider.image_lookup('image01')
        assert openstack_provider.image_lookup('123')

        mock_func.list_images.return_value = []
        with pytest.raises(OpenstackProviderError) as ex:
            openstack_provider.image_lookup('123')
        assert 'Image 123 not found!' in ex.value.args

    @staticmethod
    @mock.patch.object(OpenstackProvider, 'driver')
    def test_size_lookup(mock_func, openstack_provider):
        mock_func.list_sizes = mock.MagicMock()
        size = mock.MagicMock()
        size.name = 'large'
        size.id = 6
        mock_func.list_sizes.return_value = [size]
        assert openstack_provider.size_lookup('large')
        assert openstack_provider.size_lookup(6)

        mock_func.list_sizes.return_value = []
        with pytest.raises(OpenstackProviderError) as ex:
            openstack_provider.size_lookup('large')
        assert 'Flavor large not found!' in ex.value.args


class TestAwsProvider(object):
    @staticmethod
    def test_constructor(aws_provider):
        assert isinstance(aws_provider, AwsProvider)


class TestBeakerProvider(object):
    @staticmethod
    def test_constructor(beaker_provider):
        assert isinstance(beaker_provider, BeakerProvider)

    @staticmethod
    def test_validate_name(beaker_provider):
        assert beaker_provider.validate_name(None) is False
        assert beaker_provider.validate_name(1) is False
        assert beaker_provider.validate_name('name')

    @staticmethod
    def test_validate_timeout(beaker_provider):
        assert beaker_provider.validate_timeout(None)
        assert beaker_provider.validate_timeout(3600)
        assert beaker_provider.validate_timeout(172800)
        assert beaker_provider.validate_timeout(3599) is False
        assert beaker_provider.validate_timeout('10') is False

    @staticmethod
    def test_validate_arch(beaker_provider):
        assert beaker_provider.validate_arch('x86_64')

    @staticmethod
    def test_validate_username(beaker_provider):
        assert beaker_provider.validate_username(None)
        assert beaker_provider.validate_username('user')

    @staticmethod
    def test_validate_password(beaker_provider):
        assert beaker_provider.validate_password(None)
        assert beaker_provider.validate_password('password')

    @staticmethod
    def test_validate_tag(beaker_provider):
        assert beaker_provider.validate_tag(None)
        assert beaker_provider.validate_tag('tag')

    @staticmethod
    def test_validate_family(beaker_provider):
        assert beaker_provider.validate_family(None)
        assert beaker_provider.validate_family('family')

    @staticmethod
    def test_validate_distro(beaker_provider):
        assert beaker_provider.validate_distro(None)
        assert beaker_provider.validate_distro('distro')

    @staticmethod
    def test_validate_variant(beaker_provider):
        assert beaker_provider.validate_variant(None) is False
        assert beaker_provider.validate_variant('variant')

    @staticmethod
    def test_validate_kernel_options(beaker_provider):
        assert beaker_provider.validate_kernel_options(None)
        assert beaker_provider.validate_kernel_options(['keyboard=us'])

    @staticmethod
    def test_validate_kernel_post_options(beaker_provider):
        assert beaker_provider.validate_kernel_post_options(None)
        assert beaker_provider.validate_kernel_post_options(['timezone=set'])

    @staticmethod
    def test_validate_host_requires_options(beaker_provider):
        assert beaker_provider.validate_host_requires_options(None)
        assert beaker_provider.validate_host_requires_options(['arch=x86_64'])

    @staticmethod
    def test_validate_distro_requires_options(beaker_provider):
        assert beaker_provider.validate_distro_requires_options(None)
        assert beaker_provider.validate_distro_requires_options(
            ['arch=x86_64'])

    @staticmethod
    def test_validate_virtual_machines(beaker_provider):
        assert beaker_provider.validate_virtual_machine(None)
        assert beaker_provider.validate_virtual_machine(['True']) is False
        assert beaker_provider.validate_virtual_machine(True)

    @staticmethod
    def test_validate_virt_capable(beaker_provider):
        assert beaker_provider.validate_virt_capable(None)
        assert beaker_provider.validate_virt_capable(True)
        assert beaker_provider.validate_virt_capable('True') is False

    @staticmethod
    def test_validate_retention_tags(beaker_provider):
        assert beaker_provider.validate_retention_tag(None)
        assert beaker_provider.validate_retention_tag('Tag')
        assert beaker_provider.validate_retention_tag(10) is False

    @staticmethod
    def tests_validate_priority(beaker_provider):
        assert beaker_provider.validate_priority(None)
        assert beaker_provider.validate_priority('High')
        assert beaker_provider.validate_priority(['High']) is False

    @staticmethod
    def test_validate_whiteboard(beaker_provider):
        assert beaker_provider.validate_whiteboard(None)
        assert beaker_provider.validate_whiteboard('whiteboard')
        assert beaker_provider.validate_whiteboard(['whiteboard']) is False

    @staticmethod
    def test_validate_jobgroup(beaker_provider):
        assert beaker_provider.validate_jobgroup(None)
        assert beaker_provider.validate_jobgroup('group')
        assert beaker_provider.validate_jobgroup(['group']) is False

    @staticmethod
    def test_validate_key_values(beaker_provider):
        assert beaker_provider.validate_key_values(None)
        assert beaker_provider.validate_key_values([1, 2])
        assert beaker_provider.validate_key_values(1) is False

    @staticmethod
    def test_validate_taskparam(beaker_provider):
        assert beaker_provider.validate_taskparam(None)
        assert beaker_provider.validate_taskparam([1, 2])
        assert beaker_provider.validate_taskparam(1) is False

    @staticmethod
    def test_validate_keytab(beaker_provider):
        assert beaker_provider.validate_keytab(None)
        assert beaker_provider.validate_keytab('keytab')
        assert beaker_provider.validate_keytab(['keytab']) is False

    @staticmethod
    def test_validate_ignore_panic(beaker_provider):
        assert beaker_provider.validate_ignore_panic(None)
        assert beaker_provider.validate_ignore_panic(True)
        assert beaker_provider.validate_ignore_panic('True') is False

    @staticmethod
    def test_validate_ssh_key(beaker_provider):
        assert beaker_provider.validate_ssh_key(None)
        assert beaker_provider.validate_ssh_key('ssh-key')
        assert beaker_provider.validate_ssh_key(['ssh-key']) is False

    @staticmethod
    def test_validate_kickstsart(beaker_provider):
        assert beaker_provider.validate_kickstart(None)
        assert beaker_provider.validate_kickstart('kickstart')
        assert beaker_provider.validate_kickstart(['kickstart']) is False

    @staticmethod
    def test_validate_hostname(beaker_provider):
        assert beaker_provider.validate_hostname(None)
        assert beaker_provider.validate_hostname('hostname')
        assert beaker_provider.validate_hostname(['hostname']) is False

    @staticmethod
    def test_validate_ksmeta(beaker_provider):
        assert beaker_provider.validate_ksmeta(None)
        assert beaker_provider.validate_ksmeta('meta') is False
        assert beaker_provider.validate_ksmeta(['meta'])

    @staticmethod
    def test_validate_ip_address(beaker_provider):
        assert beaker_provider.validate_ip_address(None)
        assert beaker_provider.validate_ip_address('127.0.0.1')
        assert beaker_provider.validate_ip_address(['127.0.0.1']) is False

    @staticmethod
    def test_validate_job_id(beaker_provider):
        assert beaker_provider.validate_job_id(None)
        assert beaker_provider.validate_job_id('123')
        assert beaker_provider.validate_job_id(['123']) is False
