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
    carbon.resources.package

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from ..core import CarbonResource
from ..tasks import InstallTask, ConfigTask, ValidateTask


class Package(CarbonResource):

    _validate_task_class = ValidateTask
    _install_task_class = InstallTask
    _config_task_class = ConfigTask

    def __init__(self, data={}):
        super(Package, self).__init__(data)

        self._add_task(self._make_validate_task())
        self._add_task(self._make_install_task())
        self._add_task(self._make_config_task())

    def _make_validate_task(self):
        """
        Used to create the config attribute by the Host constructor.
        """
        task = {
            'task': self._validate_task_class,
            'name': str(self.name),
            'package': self,
            'msg': '  validating package %s' % self.name,
            'clean_msg': '  cleanup after validating package %s' % self.name
        }
        return task

    def _make_install_task(self):
        """
        Used to create the provision attribute by the Host constructor.
        """
        task = {
            'task': self._install_task_class,
            'name': str(self.name),
            'package': self,
            'msg': '  installing package %s' % self.name,
            'clean_msg': '  cleanup after installing package %s' % self.name
        }
        return task

    def _make_config_task(self):
        """
        Used to create the config attribute by the Host constructor.
        """
        task = {
            'task': self._config_task_class,
            'name': str(self.name),
            'package': self,
            'msg': '  configuring package %s' % self.name,
            'clean_msg': '  cleanup after configuring package %s' % self.name
        }
        return task
