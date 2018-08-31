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
    carbon.executor.runner

    Carbon's default and main executor.

    :copyright: (c) 2018 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import os.path
from ..core import CarbonExecutor
from ..orchestrators._ansible import Inventory


class RunnerExecutor(CarbonExecutor):
    """ The main executor for Carbon."""

    __executor_name__ = 'runner'

    # _optional_parameters = (
    #     'git',
    #     'shell',
    #     'script',
    #     'playbook',
    #     'ansible_options',
    # )

    def __init__(self, package):
        """Constructor.

        :param action: action to be executed
        :param hosts: action runs against these hosts
        :param kwargs: action parameters
        """
        super(RunnerExecutor, self).__init__()

        # set all required info here
        # set attributes
        self._name = getattr(package, 'name')
        self._desc = getattr(package, 'description')
        self._hosts = getattr(package, 'hosts')
        self.config = getattr(package, 'config')
        self.all_hosts = getattr(package, 'all_hosts')
        self.workspace = self.config['WORKSPACE']
        self.options = getattr(package, 'ansible_options', None)
        self.playbook = getattr(package, 'playbook', None)
        self.script = getattr(package, 'script', None)
        self.options = getattr(package, 'ansible_options', None)

        # create inventory object for create/delete inventory file
        self.inv = Inventory(
            self.hosts,
            self.all_hosts,
            data_dir=self.config['DATA_FOLDER']
        )


    def validate(self):
        """Validate."""
        raise NotImplementedError

    def run(self):
        """Run."""

        # create inventory if it doesn't exist
        if not os.path.exists(self.inv.master_inventory):
            self.inv.create()

        # TODO: add code to call ansible module to clone git
        self.logger.info("Clone git here")

        # TODO: add code to execute user's shell command if that is set
        self.logger.info("exec shell command here")

        # TODO: add code to execute user's playbook if that is set

        # TODO: add code to execute user's shell script if that is set

        # TODO: add code to retrieve artifacts (fetch ansible module)
        self.logger.info("Retrieve results here")
