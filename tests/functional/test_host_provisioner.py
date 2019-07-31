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
    tests.test_host_provisioner

    Unit tests for testing carbon host provisioner class.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import mock
import pytest

from carbon.resources import Asset
from carbon.core import ProvisionerPlugin, CarbonProvisioner
from carbon.provisioners import AssetProvisioner


@pytest.fixture(scope='class')
def host():
    host = mock.MagicMock(spec=Asset, name='Test-Asset', provider_params='Test Provider Params', provider_credentials='Test Cred Params')
    return host


@pytest.fixture(scope='class')
def plugin():
    pg = mock.MagicMock(spec=ProvisionerPlugin, create=mock.MagicMock('Test Asset-Provisioner Create Success'),
                        delete=mock.MagicMock('Test Asset-Provisioner Delete Success'))
    return pg


@pytest.fixture(scope='class')
def host_provisioner(host, plugin):
    hp = AssetProvisioner(host, plugin)
    return hp


class TestAssetProvisioner(object):

    @staticmethod
    def test_host_provisioner_constructor(host_provisioner):
        assert isinstance(host_provisioner, CarbonProvisioner)


    @staticmethod
    def test_host_provisioner_create(host_provisioner, plugin):
        host_provisioner.create()
        plugin.create.assert_called()


    @staticmethod
    def test_host_provisioner_delete(host_provisioner, plugin):
        host_provisioner.delete()
        plugin.delete.assert_called()

    @staticmethod
    @mock.patch.object(CarbonProvisioner, 'logger')
    def test_host_provisioner_print_common_attributes(mock_logger, host_provisioner):
        mock_logger.debug = mock.MagicMock()
        host_provisioner.print_commonly_used_attributes()
        mock_logger.debug.assert_called()


    @staticmethod
    def test_host_provisioner_create_exception(host_provisioner, plugin):
        plugin.create.side_effect = Exception('Mock Create Failure')
        with pytest.raises(Exception):
            host_provisioner.create()

    @staticmethod
    def test_host_provisioner_delete_exception(host_provisioner, plugin):
        plugin.delete.side_effect = Exception('Mock Delete Failure')
        with pytest.raises(Exception):
            host_provisioner.delete()