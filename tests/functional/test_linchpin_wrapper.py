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
import mock
import pytest

from carbon.resources import Host
from carbon.core import CarbonProvisioner
from carbon.exceptions import CarbonProvisionerError
from carbon.provisioners import LinchpinWrapperProvisioner
from linchpin import LinchpinAPI


@pytest.fixture
def host_params():
  return dict(
      role='client',
      provider=dict(
          name='openstack',
          credential='openstack',
          image='image',
          flavor='small',
          networks=['network'],
          keypair='key',
          floating_ip_pool='pool'
      )
  )

@pytest.fixture
def host(host_params, config):
  return Host(
      name='host01',
      config=config,
      provisioner='linchpin-wrapper',
      parameters=copy.deepcopy(host_params)
  )

@pytest.fixture
def linchpin_wrapper(host):
  return LinchpinWrapperProvisioner(host)


class TestLinchpinWrapperProvisioner(object):

  def up(*args, **kwargs):
    return (0, {'carbon':{'inputs': {}, 'outputs': { 'resources': {}}}})

  def destroy(*args, **kwargs):
    return True

  def up_failed(*args, **kwargs):
    return (1, {'carbon':{'inputs': {}, 'outputs': { 'resources': {}}}})

  def run_data(*args, **kwargs):
    resources = {'os_server_res': [{'servers':[{
        'interface_ip': '1.1.1.1',
        'id': '1'
        }]}]}
    return {'carbon':{'inputs': {}, 'outputs': { 'resources': resources }}}

  @staticmethod
  def test_linchpin_wrapper_constructor(linchpin_wrapper):
    assert isinstance(linchpin_wrapper, LinchpinWrapperProvisioner)

  @staticmethod
  @mock.patch.object(LinchpinAPI, 'do_action', destroy)
  def test_linchpin_wrapper_delete(linchpin_wrapper):
    linchpin_wrapper.delete()

  @staticmethod
  @mock.patch.object(LinchpinAPI, 'do_action', up_failed)
  @mock.patch.object(LinchpinAPI, 'get_run_data', run_data)
  def test_linchpin_wrapper_failed_create(linchpin_wrapper):
    with pytest.raises(CarbonProvisionerError):
      linchpin_wrapper.create()

  @staticmethod
  @mock.patch.object(LinchpinAPI, 'do_action', up)
  @mock.patch.object(LinchpinAPI, 'get_run_data', run_data)
  def test_linchpin_wrapper_create(linchpin_wrapper):
    linchpin_wrapper.create()
    assert getattr(linchpin_wrapper.host, 'ip_address') == "1.1.1.1"