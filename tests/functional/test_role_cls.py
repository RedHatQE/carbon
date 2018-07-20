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
    Unit tests to test ansible orchestrator's role class.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import unittest
from copy import copy

from ansible.cli.galaxy import GalaxyCLI
from ansible.errors import AnsibleOptionsError
from nose.tools import nottest, raises

from carbon.orchestrators._ansible import Role


class TestRoleClass(unittest.TestCase):

    @raises(AnsibleOptionsError)
    def test_create_invalid_galaxy_cli(self):
        Role('foo')

    def test_create_valid_galaxy_cli(self):
        self.assertIsInstance(Role('info').cli, GalaxyCLI)

    def test_update_command_options(self):
        default_options = dict(force=False)
        user_options = dict(force=True)

        role = Role('info')
        options = role._update_options(copy(default_options), user_options)
        assert not default_options == options

    def test_set_galaxy_cli_options(self):
        role = Role('install')
        role._set_galaxy_cli_options(dict(force=True))

    def test_invalid_install_null_role(self):
        role = Role('install')
        rc = role.install()
        self.assertEqual(rc, 1)

    def test_invalid_install_role(self):
        role = Role('install')
        rc = role.install(role='invalid.role')
        self.assertEqual(rc, 1)

    def test_install_role(self):
        role = Role('install')
        rc = role.install(role='davidwittman.redis', options=dict(force=True))
        self.assertEqual(rc, 0)

    def test_install_role_file(self):
        role = Role('install')
        rc = role.install(
            role_file='workspace/role.yml',
            options=dict(force=True)
        )
        self.assertEqual(rc, 0)

    def test_invalid_remove_null_role(self):
        role = Role('remove')
        rc = role.remove()
        self.assertEqual(rc, 1)

    def test_invalid_remove_role(self):
        role = Role('remove')
        rc = role.remove(role='invalid.role')
        self.assertEqual(rc, 0)

    def test_remove_role(self):
        self.test_install_role()
        role = Role('remove')
        rc = role.remove(role='davidwittman.redis')
        self.assertEqual(rc, 0)

    @nottest
    def test_remove_role_file(self):
        # TODO: this test fails when running python2 & 3 test env at once (fix)
        self.test_install_role_file()
        role = Role('remove')
        rc = role.remove(role_file='workspace/role.yml')
        self.assertEqual(rc, 0)

    def test_remove_mia_role_file(self):
        role = Role('remove')
        rc = role.remove(role_file='mia.yml')
        self.assertEqual(rc, 1)


if __name__ == '__main__':
    unittest.main()
