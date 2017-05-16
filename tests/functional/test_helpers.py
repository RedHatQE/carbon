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
    Unit tests to test carbon helpers.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from nose.tools import assert_is_instance, assert_equal, assert_is, raises
from nose.tools import assert_not_equal, assert_is_not

from carbon import Carbon
from carbon.helpers import AnsibleWorker, CarbonCallback, file_mgmt
from carbon.helpers import get_provisioner_class, get_provisioners_classes
from carbon.helpers import get_provider_class, get_providers_classes
from carbon.providers import OpenstackProvider
from carbon.provisioners import LinchpinProvisioner


class TestLogging(object):
    """Unit test to test carbon logging."""

    @staticmethod
    def test_logger_cache():
        """Test carbons logger."""
        cbn = Carbon(__name__)
        logger1 = cbn.logger
        assert_is(cbn.logger, logger1)
        assert_equal(cbn.name, __name__)
        cbn.logger_name = __name__ + '/test_logger_cache'
        assert_is_not(cbn.logger, logger1)


class TestFileManagement(object):
    """Unit tests to test carbons file management function."""

    @staticmethod
    @raises(Exception)
    def test_unknown_file_operation():
        """Test carbons file management function with an invalid operaton. An
        exception will be raised.
        """
        file_mgmt('x', 'test.yml')

    @staticmethod
    @raises(Exception)
    def test_file_not_found():
        """Test carbons file management function attempting to read a file
        that does not exist. An exception will be raised.
        """
        file_mgmt('r', 'test.yml')

    @staticmethod
    def test_yaml_file_extension():
        """Test carbons file management function attempting to read/write a
        yaml file type.
        """
        _file = "test.yml"
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            file_mgmt('w', _file, _data)
            assert_is_instance(file_mgmt('r', _file), dict)
        finally:
            os.remove(_file)

    @staticmethod
    def test_json_file_extension():
        """Test carbons file management function attempting to read/write a
        json file type.
        """
        _file = "test.json"
        _data = {'name': 'carbon', 'group': [{'name': 'group'}]}
        try:
            file_mgmt('w', _file, _data)
            assert_is_instance(file_mgmt('r', _file), dict)
        finally:
            os.remove(_file)

    @staticmethod
    def test_txt_file_extension():
        """Test carbons file management function attempting to read/write a
        txt file type.
        """
        _file = "test.txt"
        _data = "Carbon project"
        try:
            file_mgmt('w', _file, _data)
            assert_equal(file_mgmt('r', _file), "Carbon project")
        finally:
            os.remove(_file)

    @staticmethod
    def test_ini_file_extension():
        """Test carbons file management function attempting to read/write a
        ini file type.
        """
        _file = "test.ini"
        cfg1, cfg2 = ConfigParser(), ConfigParser()
        cfg1.add_section('Carbon')
        cfg1.set('Carbon', 'Team', 'PIT')
        try:
            file_mgmt('w', _file, cfg_parser=cfg1)
            file_mgmt('r', _file, cfg_parser=cfg2)
            assert_is_instance(cfg2, ConfigParser)
        finally:
            os.remove(_file)


class TestGetModuleClasses(object):
    """Unit tests to test carbon functions that get classes or a class from
    carbon modules.
    """

    @staticmethod
    def test_get_provisioners_classes():
        """Test the function to get all provisioner classes. It checks if the
        length of the list returned is not zero.
        """
        provisioners = get_provisioners_classes()
        assert_not_equal(len(provisioners), 0)

    @staticmethod
    def test_get_provisioner_class():
        """Test the function to get a provisioner class. It will attempt to
        get the linchpin provisioner class and then verify that the class
        returned is the linchpin provisioner class.
        """
        provisioner = get_provisioner_class('linchpin')
        assert_is(provisioner, LinchpinProvisioner)

    @staticmethod
    def test_get_providers_classes():
        """Test the function to get all provider classes. It checks if the
        length of the list returned is not zero.
        """
        providers = get_providers_classes()
        assert_not_equal(len(providers), 0)

    @staticmethod
    def test_get_provider_class():
        """Test the function to get a provider class. It will attempt to get
        the openstack provider class and then verify that the class returned
        is the openstack provider class.
        """
        provider = get_provider_class('openstack')
        assert_is(provider, OpenstackProvider)


class TestAnsible(object):
    """Unit tests to test Ansible worker class."""

    @staticmethod
    def test_create_ansible_object():
        """Test creating a new Ansible worker object. It will verify the
        object created is an instance of the Ansible worker class.
        """
        obj = AnsibleWorker()
        assert_is_instance(obj, AnsibleWorker)

    @staticmethod
    def test_run_module_pass():
        """Test the run_module method executing a command successfully. This
        test performs the following:
            1. Create Ansible worker object.
            2. Call the method with the play source.
            3. Verify the return code and callback object.
        """
        obj = AnsibleWorker()
        returncode, callback = obj.run_module(
            dict(name='Module example',
                 hosts='localhost',
                 gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args='whoami'))])
        )
        assert_equal(returncode, 0)
        assert_is_instance(callback, CarbonCallback)

    @staticmethod
    def test_run_module_fail():
        """Test the run_module method executing a command unsuccessfully. This
        test performs the following:
            1. Create Ansible worker object.
            2. Call the method with the play source.
            3. Verify the return code and callback object.
        """
        obj = AnsibleWorker()
        returncode, callback = obj.run_module(
            dict(name='Module example',
                 hosts='localhost',
                 gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args='whoamx'))])
        )
        assert_not_equal(returncode, 0)
        assert_is_instance(callback, CarbonCallback)

    @staticmethod
    def test_run_module_unreachable():
        """Test the run_module method when a host is unreachable. This test
        performs the following:
            1. Create a mock inventory file.
            2. Create the Ansible worker object.
            3. Call the method with the play source.
            4. Verify the return code and callback object.
            5. Delete the mock inventory file.
        """
        host = 'machine1'
        inventory = '/tmp/tmp_inventory'

        # Create tmp inventory file
        config = ConfigParser()
        config.add_section(host)
        config.set(host, '192.168.1.1', 'None')
        file_mgmt('w', inventory, cfg_parser=config)
        fdata = file_mgmt('r', inventory)
        fdata = fdata.replace(' = None', '')
        file_mgmt('w', inventory, fdata)

        obj = AnsibleWorker(inventory)
        returncode, callback = obj.run_module(
            dict(name='Module example',
                 hosts=host,
                 gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args='whoamx'))])
        )
        assert_not_equal(returncode, 0)
        assert_is(callback.unreachable, True)

        # Remove tmp inventory file
        os.remove(inventory)

    @staticmethod
    def test_run_playbook_pass():
        """Test the run_playbook method executing a playbook successfully.
        This test performs the following:
            1. Create a mock playbook.
            2. Create the Ansible worker object.
            3. Call the method with the playbook.
            4. Verify the return code and callback object.
            5. Delete the mock playbook.
        """
        pb_file = '/tmp/example.yaml'
        extra_vars = {'name': 'carbon'}

        # Create tmp playbook
        pbdata = [{'tasks': [{'shell': 'whoami', 'register': 'result'}],
                   'hosts': 'localhost', 'gather_facts': 'no'}]
        file_mgmt('w', pb_file, pbdata)

        obj = AnsibleWorker()
        returncode, callback = obj.run_playbook(pb_file, extra_vars=extra_vars)

        assert_equal(returncode, 0)
        assert_is_instance(callback, CarbonCallback)

        # Remove tmp playbook
        os.remove(pb_file)

    @staticmethod
    def test_run_playbook_fail():
        """Test the run_playbook method executing a playbook unsuccessfully.
        This test performs the following:
            1. Create a mock playbook.
            2. Create the Ansible worker object.
            3. Call the method with the playbook.
            4. Verify the return code and callback object.
            5. Delete the mock playbook.
        """
        pb_file = '/tmp/example.yaml'
        pb_retry = '/tmp/example.retry'
        extra_vars = {'name': 'carbon'}

        # Create tmp playbook
        pbdata = [{'tasks': [{'shell': 'whoamx', 'register': 'result'}],
                   'hosts': 'localhost', 'gather_facts': 'no'}]
        file_mgmt('w', pb_file, pbdata)

        obj = AnsibleWorker()
        returncode, callback = obj.run_playbook(pb_file, extra_vars=extra_vars)

        assert_not_equal(returncode, 0)
        assert_is_instance(callback, CarbonCallback)

        # Remove tmp playbook
        for item in [pb_file, pb_retry]:
            os.remove(item)
