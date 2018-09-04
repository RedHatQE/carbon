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
from ..orchestrators._ansible import Inventory, AnsibleController
from ..helpers import get_ans_verbosity


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

        :param package: execute resource
        :type package: object
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
        self.datadir = self.config['DATA_FOLDER']
        self.playbook = getattr(package, 'playbook', None)
        self.script = getattr(package, 'script', None)
        self.shell = getattr(package, 'shell', None)
        self.git = getattr(package, 'git', None)
        self.artifacts = getattr(package, 'artifacts')
        self.options = getattr(package, 'ansible_options', None)

        # set ansible attributes
        self.__set_ansible_attr__()

    def __set_ansible_attr__(self):
        """Set commonly used class attributes for ansible."""
        # create inventory object for create/delete inventory file
        self.inv = Inventory(
            self.hosts,
            self.all_hosts,
            data_dir=self.config['DATA_FOLDER']
        )

        self.ans_verbosity = get_ans_verbosity(self.logger, self.config)
        self.ans_controller = AnsibleController(self.inv.inventory_dir)
        self.ans_extra_vars = dict(hosts=self.inv.group)

    def validate(self):
        """Validate."""
        raise NotImplementedError

    @staticmethod
    def build_ans_extra_args(attr, keys):
        """Build ansible extra arguments for ansible ad hoc commands.

        :param attr: key/values defined by task input
        :type attr: dict
        :param keys: keys used to build extra args
        :type keys: list
        :return: extra args
        :rtype: str
        """
        extra_args = ''
        for key in attr:
            if key in keys:
                extra_args += '%s=%s ' % (key, attr[key])
        return extra_args

    def __git__(self):
        """Clone git repositories."""
        # TODO: move these into constants
        keys = ["repo", "version", "dest"]

        extra_args = self.build_ans_extra_args(self.git, keys)

        results = self.ans_controller.run_module(
            "git",
            logger=self.logger,
            extra_vars=self.ans_extra_vars,
            # run_options=run_options,
            extra_args=extra_args,
            ans_verbosity=self.ans_verbosity
        )

        # TODO: what to do with cloning results - fail on error
        self.logger.info(results)

    def __shell__(self):
        """Execute the shell command."""
        self.logger.info("running shell cmds here")

        # execute the shell cmds one at a time
        for shell in self.shell:
            self.logger.info("Running shell cmd")
            # create an ansible controller object

            extra_args = self.build_ans_extra_args(self.shell, ['chdir'])

            results = self.ans_controller.run_module(
                "shell",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                # run_options=run_options,
                script=shell["command"],
                extra_args=extra_args,
                ans_verbosity=self.ans_verbosity
            )

            # TODO: what to do with shell results - fail on error??
            self.logger.info(results)

    def __script__(self):
        """Execute the script supplied."""
        raise NotImplementedError

    def __playbook__(self):
        """Execute the playbook supplied."""
        raise NotImplementedError

    def __artifacts__(self):
        """Archive artifacts produced by the tests."""
        results = None
        dest = os.path.join(self.datadir, 'artifacts')
        self.logger.debug("Retrieve results here")
        self.logger.debug("Storing results in %s" % dest)

        for src_artifact in self.artifacts:
            extra_args = "src=%s dest=%s mode=pull" % (src_artifact, dest)

            results = self.ans_controller.run_module(
                "synchronize",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                # run_options=run_options,
                extra_args=extra_args,
                ans_verbosity=self.ans_verbosity
            )

        # TODO: what to do with archive results - fail on error
        self.logger.info(results)

    def run(self):
        """Run.

        The run method is the main entry point for the runner executor. This
        method will invoke various other methods in order to successfully
        run the runners execute types given.
        """

        # create inventory if it doesn't exist
        if not os.path.exists(self.inv.master_inventory):
            self.inv.create()

        # TODO: dynamically get the attribute names
        for attr in ['git', 'shell', 'playbook', 'script', 'artifacts']:
            # skip if the execute resource does not have the attribute defined
            if not getattr(self, attr):
                continue

            # call the method associated to the execute resource attribute
            getattr(self, '__%s__' % attr)()
