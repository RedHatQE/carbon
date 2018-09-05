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
from ..exceptions import ArchiveArtifactsError, CarbonExecuteError
from ..orchestrators._ansible import Inventory, AnsibleController
from ..helpers import get_ans_verbosity

# TODO: pass ansible options to each ad hoc call


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

    _execute_types = [
        'playbook',
        'script',
        'shell'
    ]

    def __init__(self, package):
        """Constructor.

        :param package: execute resource
        :type package: object
        """
        super(RunnerExecutor, self).__init__()

        # set required attributes
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
        self.logger.warning('GIT PACKAGE MUST BE INSTALLED ON REMOTE HOSTS!')

        for item in self.git:
            # build extra args
            extra_args = self.build_ans_extra_args(
                item, ["repo", "version", "dest"])

            results = self.ans_controller.run_module(
                "git",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                extra_args=extra_args,
                ans_verbosity=self.ans_verbosity
            )

            if results[0] != 0:
                raise CarbonExecuteError('Clone git repository %s failed!' %
                                         item['repo'])

    def __shell__(self):
        """Execute the shell command."""
        self.logger.info('Executing shell commands:')

        for index, shell in enumerate(self.shell):
            index += 1
            self.logger.info('%s. %s' % (index, shell['command']))

            extra_args = self.build_ans_extra_args(self.shell, ['chdir'])

            results = self.ans_controller.run_module(
                "shell",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                script=shell['command'],
                extra_args=extra_args,
                ans_verbosity=self.ans_verbosity
            )

            if results[0] != 0:
                raise ArchiveArtifactsError('Shell command %s failed to run '
                                            'successfully!' % shell['command'])

    def __script__(self):
        """Execute the script supplied."""
        self.logger.info('Executing scripts:')

        for index, script in enumerate(self.script):
            index += 1
            self.logger.info('%s. %s' % (index, script['name']))

            extra_args = self.build_ans_extra_args(self.script, ['chdir'])

            results = self.ans_controller.run_module(
                "script",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                script=script['name'],
                extra_args=extra_args,
                ans_verbosity=self.ans_verbosity
            )

            if results[0] != 0:
                raise ArchiveArtifactsError(
                    'Script %s failed to run successfully!' % script['name']
                )

    def __playbook__(self):
        """Execute the playbook supplied."""
        # TODO: implementation!
        self.logger.info('Executing playbooks:')

        for index, pb in enumerate(self.playbook):
            index += 1
            self.logger.info('%s. %s' % (index, pb['name']))

            results = self.ans_controller.run_playbook(pb)

            if results[0] != 0:
                raise ArchiveArtifactsError(
                    'Playbook %s failed to run successfully!' % pb['name']
                )

    def __artifacts__(self):
        """Archive artifacts produced by the tests."""
        # TODO: do we want to have a dir per remote host
        # TODO: follow up on Vimal's email regarding issues
        dest = os.path.join(self.datadir, 'artifacts')

        if not os.path.exists(dest):
            os.makedirs(dest)

        self.logger.info('Archiving test artifacts @ %s:' % dest)

        for index, artifact in enumerate(self.artifacts):
            index += 1
            self.logger.info('%s. %s' % (index, artifact))

            extra_args = "src=%s dest=%s mode=pull" % (artifact, dest)

            results = self.ans_controller.run_module(
                "synchronize",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                extra_args=extra_args,
                ans_verbosity=self.ans_verbosity
            )

            if results[0] != 0:
                raise CarbonExecuteError(
                    'Failed to archive artifact: %s' % artifact
                )

    def run(self):
        """Run.

        The run method is the main entry point for the runner executor. This
        method will invoke various other methods in order to successfully
        run the runners execute types given.
        """

        # create inventory if it doesn't exist
        if not os.path.exists(self.inv.master_inventory):
            self.inv.create()

        for attr in ['git', 'shell', 'playbook', 'script', 'artifacts']:
            # skip if the execute resource does not have the attribute defined
            if not getattr(self, attr):
                continue

            # call the method associated to the execute resource attribute
            try:
                getattr(self, '__%s__' % attr)()
            except ArchiveArtifactsError as ex:
                # test execution failed, test artifacts may still have been
                # generated. lets go ahead and archive these for debugging
                # purposes
                self.logger.error(ex.message)
                self.logger.info('Fetching test generated artifacts')
                self.__artifacts__()
