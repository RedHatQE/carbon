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
import os
from unittest import TestCase

try:
    from test.test_support import EnvironmentVarGuard
except ImportError:
    from test.support import EnvironmentVarGuard

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from nose.tools import assert_is_instance, assert_true, assert_false, assert_is
from nose.tools import assert_is_none, assert_not_equal, assert_equal, raises

from carbon._compat import string_types
from carbon.controllers import AnsibleController, CarbonCallback
from carbon.controllers import DockerController, DockerControllerException
from carbon.helpers import file_mgmt


class TestDockerController(TestCase):
    """Unit tests to test docker controller."""

    @staticmethod
    def test_create_object():
        """Test creating a docker controller object."""
        assert_is_instance(DockerController(), DockerController)

    @staticmethod
    @raises(DockerControllerException)
    def test_get_container():
        """Test method to get container object."""
        _name = 'kingbob'
        obj = DockerController()

        # Container present
        obj.run_container(_name, 'fedora', command='bash')
        obj.get_container(_name)
        obj.stop_container(_name)
        obj.remove_container(_name)

        # Container absent
        obj.get_container('kevin')

    @staticmethod
    def test_get_image():
        """Test method to get image."""
        obj = DockerController()

        # Container present
        assert_true(obj.get_image('fedora'))

        # Container absent
        assert_false(obj.get_image('fadora'))

    @staticmethod
    def test_get_container_status():
        """Test method to get container status."""
        _name = 'stuart'
        _image = 'fedora'
        obj = DockerController()

        # Container present
        obj.pull_image(_image)
        obj.run_container(_name, _image, command='bash')
        assert_is_instance(obj.get_container_status(_name), string_types)
        obj.stop_container(_name)
        obj.remove_container(_name)

        # Container absent
        assert_is_none(obj.get_container_status(_name))

    @staticmethod
    @raises(DockerControllerException)
    def test_remove_image():
        """Test method to remove an image."""
        _image = 'alpine'
        obj = DockerController()

        # Image present
        obj.pull_image(_image)
        obj.remove_image(_image)

        # Image absent
        obj.remove_image('fadora')

    @staticmethod
    @raises(DockerControllerException)
    def test_pull_image():
        """Test method to pull an image."""
        obj = DockerController()

        # Image present
        obj.pull_image('alpine')

        # Image absent
        obj.pull_image('fadora')

    @staticmethod
    def test_stop_container():
        """Test method to stop a container."""
        _name = 'bob'
        _image = 'fedora'
        obj = DockerController()

        # Container present
        obj.pull_image(_image)
        obj.run_container(_name, _image, command='bash')
        obj.stop_container(_name)
        obj.remove_container(_name)

        # Container absent
        obj.stop_container(_name)

    @staticmethod
    def test_start_container():
        """Test method to start a container."""
        _name = 'stewie'
        _image = 'fedora'
        obj = DockerController()

        # Container present
        obj.pull_image(_image)
        obj.run_container(_name, _image, command='bash')
        obj.start_container(_name)
        obj.stop_container(_name)
        obj.start_container(_name)
        obj.stop_container(_name)
        obj.remove_container(_name)

    @staticmethod
    def test_run_container():
        """Test method to run a command in a new container."""
        _name = 'peter'
        _image = 'fedora'
        obj = DockerController()

        obj.pull_image(_image)

        # Container present and running
        try:
            obj.run_container(_name, _image, command='bash')
            obj.run_container(_name, _image, command='bash')
        except DockerControllerException:
            pass

        # Container present and exited
        obj.stop_container(_name)
        obj.run_container(_name, _image, command='bash')
        obj.stop_container(_name)
        obj.remove_container(_name)


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
        inventory = '/tmp/tmp_inventory'

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

        obj = AnsibleController()
        results = obj.run_playbook(pb_file, extra_vars=extra_vars)

        assert_equal(results['status'], 0)
        assert_is_instance(results['callback'], CarbonCallback)

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

        obj = AnsibleController()
        results = obj.run_playbook(pb_file, extra_vars=extra_vars)

        assert_not_equal(results['status'], 0)
        assert_is_instance(results['callback'], CarbonCallback)

        # Remove tmp playbook
        for item in [pb_file, pb_retry]:
            os.remove(item)
