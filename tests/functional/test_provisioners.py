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
    tests.test_provisioners

    Unit tests for testing carbon provisioner classes.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from carbon.provisioners import StaticProvisioner, OpenstackProvisioner


@pytest.fixture(scope='class')
def provisioner_static():
    host = mock.MagicMock()
    host.static_ip_address = '127.0.0.1'
    host.static_hostname = 'host01'

    return StaticProvisioner(host)


@pytest.fixture(scope='class')
def openstack_provisioner():
    host = mock.MagicMock()
    host.os_name = 'node01'
    host.os_image = 'image01'
    host.os_flavor = 'large'
    host.os_networks = 'internal'
    host.os_floating_ip_pool = 'public'

    return OpenstackProvisioner(host)


class TestStaticProvisioner(object):
    @staticmethod
    def test_constructor(provisioner_static):
        assert isinstance(provisioner_static, StaticProvisioner)

    @staticmethod
    def test_create(provisioner_static):
        provisioner_static.create()

    @staticmethod
    def test_delete(provisioner_static):
        provisioner_static.delete()


class TestOpenstackProvisioner(object):
    @staticmethod
    def test_constructor(openstack_provisioner):
        assert isinstance(openstack_provisioner, OpenstackProvisioner)

    @staticmethod
    def test_create(openstack_provisioner):
        provider = mock.MagicMock()
        provider._create = mock.MagicMock()
        provider._create.return_value = '127.0.0.1', '123'
        openstack_provisioner.host.provider = provider
        openstack_provisioner.create()

    @staticmethod
    def test_delete(openstack_provisioner):
        provider = mock.MagicMock()
        provider._delete = mock.MagicMock()
        provider._delete.return_value = True
        openstack_provisioner.delete()
