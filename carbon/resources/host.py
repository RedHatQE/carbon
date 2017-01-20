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
    carbon.resources.host

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from ..helpers import Resource
from ..tasks import ProvisionTask, TeardownTask, ConfigTask


class Host(Resource):

    _task_provision_class = ProvisionTask
    _task_config_class = ConfigTask
    _task_teardown_class = TeardownTask

    def __init__(self, data={}):
        super(Host, self).__init__(data)

    def make_provision(self):
        """
        Used to create the provision attribute by the Host constructor.
        """
        return self._task_provision_class()

    def make_config(self):
        """
        Used to create the config attribute by the Host constructor.
        """
        return self._task_config_class()

    def make_teardown(self):
        """
        Used to create the teardown attribute by the Host constructor.
        """
        return self._task_teardown_class()

    def provision(self):
        raise NotImplementedError

    def config(self):
        raise NotImplementedError

    def teardown(self):
        raise NotImplementedError
