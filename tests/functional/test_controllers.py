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
    Unit tests to test carbon controllers.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import errno
from unittest import TestCase

import os

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from nose.tools import assert_is_instance, assert_is
from nose.tools import assert_not_equal, assert_equal

from carbon.controllers import AnsibleController, CarbonCallback
from carbon.helpers import file_mgmt, gen_random_str


class TestAnsibleController(TestCase):
    """Unit tests to test Ansible controller class."""

    @staticmethod
    def test_create_object():
        """Test creating a new Ansible controller object. It will verify the
        object created is an instance of the Ansible worker class.
        """
        obj = AnsibleController()
        assert_is_instance(obj, AnsibleController)

    @staticmethod
    def test_run_module_pass():
        """Test the run_module method executing a command successfully. This
        test performs the following:
            1. Create Ansible worker object.
            2. Call the method with the play source.
            3. Verify the return code and callback object.
        """
        obj = AnsibleController()
        results = obj.run_module(
            dict(name='Module example',
                 hosts='localhost',
                 gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args='whoami'))])
        )
        assert_equal(results['status'], 0)
        assert_is_instance(results['callback'], CarbonCallback)

    @staticmethod
    def test_run_module_fail():
        """Test the run_module method executing a command unsuccessfully. This
        test performs the following:
            1. Create Ansible worker object.
            2. Call the method with the play source.
            3. Verify the return code and callback object.
        """
        obj = AnsibleController()
        results = obj.run_module(
            dict(name='Module example',
                 hosts='localhost',
                 gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args='whoamx'))])
        )
        assert_not_equal(results['status'], 0)
        assert_is_instance(results['callback'], CarbonCallback)

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
        inventory = '/tmp/tmp_inventory_{}'.format(gen_random_str(8))

        # Create tmp inventory file
        config = ConfigParser()
        config.add_section(host)
        config.set(host, '192.168.1.1', 'None')
        file_mgmt('w', inventory, cfg_parser=config)
        fdata = file_mgmt('r', inventory)
        fdata = fdata.replace(' = None', '')
        file_mgmt('w', inventory, fdata)

        obj = AnsibleController(inventory)
        results = obj.run_module(
            dict(name='Module example',
                 hosts=host,
                 gather_facts='no',
                 tasks=[dict(action=dict(module='shell', args='whoamx'))])
        )
        assert_not_equal(results['status'], 0)
        assert_is(results['callback'].unreachable, True)

        # Remove tmp inventory file
        try:
            os.remove(inventory)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

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
        pb_file = '/tmp/example_{}.yaml'.format(gen_random_str(8))

        # Create tmp playbook
        pbdata = [{'tasks': [{'shell': 'whoami', 'register': 'result'}],
                   'hosts': 'localhost', 'gather_facts': 'no'}]
        file_mgmt('w', pb_file, pbdata)

        obj = AnsibleController()
        results = obj.run_playbook(pb_file)

        assert_equal(results['status'], 0)
        assert_is_instance(results['callback'], CarbonCallback)

        # Remove tmp playbook
        try:
            os.remove(pb_file)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

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
        pb_file = '/tmp/example_{}.yaml'.format(gen_random_str(8))
        pb_retry = '/tmp/example_().retry'.format(gen_random_str(8))

        # Create tmp playbook
        pbdata = [{'tasks': [{'shell': 'whoamx', 'register': 'result'}],
                   'hosts': 'localhost', 'gather_facts': 'no'}]
        file_mgmt('w', pb_file, pbdata)

        obj = AnsibleController()
        results = obj.run_playbook(pb_file)

        assert_not_equal(results['status'], 0)
        assert_is_instance(results['callback'], CarbonCallback)

        # Remove tmp playbook
        for item in [pb_file, pb_retry]:
            try:
                os.remove(item)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise
