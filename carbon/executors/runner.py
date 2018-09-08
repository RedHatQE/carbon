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

import copy
import os.path

from ruamel.yaml import YAML

from ..core import CarbonExecutor
from ..exceptions import ArchiveArtifactsError, CarbonExecuteError
from ..helpers import get_ans_verbosity
from ..orchestrators._ansible import Inventory, AnsibleController
from ..static.playbooks import GIT_CLONE_PLAYBOOK, SYNCHRONIZE_PLAYBOOK


class RunnerExecutor(CarbonExecutor):
    """ The main executor for Carbon.

    The runner class provides three different types on how you can execute
    tests. Its intention is to be generic enough where you just need to supply
    your test commands and it will process them. All tests executed against
    remote hosts will be run through ansible.
    """

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

    user_run_vals = ["become", "become_method", "become_user", "remote_user",
                     "connection", "forks", "tags"]

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

    def build_ans_extra_args(self, attr, keys):
        """Build ansible extra arguments for ansible ad hoc commands.

        :param attr: key/values defined by task input
        :type attr: dict
        :param keys: keys used to build extra args
        :type keys: list
        :return: extra args
        :rtype: str
        """
        extra_args = ''

        if self.options and 'extra_args' in self.options and self.options['extra_args']:
            extra_args = '%s ' % self.options['extra_args']

        for key in attr:
            if key in keys:
                extra_args += '%s=%s ' % (key, attr[key])

        return extra_args

    def build_run_options(self):
        """Build ansible run options for ansible ad hoc commands.

        :return: run options
        :rtype: dict
        """

        run_options = {}

        # override ansible options (user passed in vals for specific action)
        for val in self.user_run_vals:
            if self.options and val in self.options and self.options[val]:
                run_options[val] = self.options[val]

        self.logger.debug("Ansible options used: " + str(run_options))

        return run_options

    def build_extra_vars(self):
        """Build ansible extra vars for ansible ad hoc commands.

        :return: extra args
        :rtype: str
        """

        extra_vars = {}

        if self.options and 'extra_vars' in self.options and self.options['extra_vars']:
            extra_vars.update(self.options['extra_vars'])

        if self._hosts:
            extra_vars["localhost"] = False
        else:
            extra_vars["localhost"] = True

        return extra_vars

    @staticmethod
    def _create_playbook(playbook, playbook_str):
        """Create the playbook on disk from string.

        :param playbook: playbook name
        :type playbook: str
        :param playbook_str: playbook content
        :type playbook_str: str
        """
        yaml = YAML()
        yaml.default_flow_style = False
        with open(playbook, 'w') as f:
            yaml.dump(yaml.load(playbook_str), f)

    def __git__(self):
        """Clone git repositories.

        This method takes a string formatted playbook, writes it to disk,
        provides the git details to the playbook and runs it. The result is
        on the targeted remote hosts will have the defined gits cloned for
        test execution.
        """
        # dynamic playbook
        playbook = 'cbn_clone_git.yml'

        self.logger.info('Cloning git repositories.')

        # set playbook variables
        extra_vars = copy.deepcopy(self.ans_extra_vars)
        extra_vars['gits'] = self.git

        # create dynamic playbook
        self._create_playbook(playbook, GIT_CLONE_PLAYBOOK)

        # run playbook
        results = self.ans_controller.run_playbook(
            playbook,
            logger=self.logger,
            extra_vars=extra_vars,
            ans_verbosity=self.ans_verbosity
        )

        # remove dynamic playbook
        os.remove(playbook)

        if results[0] != 0:
            raise CarbonExecuteError('Failed to clone git repositories!')

    def __shell__(self):
        """Execute the shell command."""
        self.logger.info('Executing shell commands:')

        for index, shell in enumerate(self.shell):
            index += 1
            self.logger.info('%s. %s' % (index, shell['command']))

            extra_args = self.build_ans_extra_args(shell, ['chdir'])

            # build run options
            run_options = self.build_run_options()

            # update extra vars
            self.ans_extra_vars.update(self.build_extra_vars())

            results = self.ans_controller.run_module(
                "shell",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                script=shell['command'],
                run_options=run_options,
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

            extra_args = self.build_ans_extra_args(script, ['chdir'])

            # update extra vars
            self.ans_extra_vars.update(self.build_extra_vars())

            # build run options
            run_options = self.build_run_options()

            results = self.ans_controller.run_module(
                "script",
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                script=script['name'],
                run_options=run_options,
                extra_args=extra_args,
                ans_verbosity=self.ans_verbosity
            )

            if results[0] != 0:
                raise ArchiveArtifactsError(
                    'Script %s failed to run successfully!' % script['name']
                )

    def __playbook__(self):
        """Execute the playbook supplied."""
        self.logger.info('Executing playbooks:')

        # update extra vars
        self.ans_extra_vars.update(self.build_extra_vars())

        # build run options
        run_options = self.build_run_options()

        for index, playbook in enumerate(self.playbook):
            index += 1
            self.logger.info('%s. %s' % (index, playbook['name']))

            # run playbook
            results = self.ans_controller.run_playbook(
                playbook,
                logger=self.logger,
                extra_vars=self.ans_extra_vars,
                run_options=run_options,
                ans_verbosity=self.ans_verbosity
            )

            if results[0] != 0:
                raise ArchiveArtifactsError('Failed to run playbook %s '
                                            'successfully!' % playbook['name'])

    def __artifacts__(self):
        """Archive artifacts produced by the tests.

        This method takes a string formatted playbook, writes it to disk,
        provides the test artifacts details to the playbook and runs it. The
        result is on the machine where carbon is run, all test artifacts will
        be archived inside the data folder.

        Example artifacts archive structure:

        artifacts/
            host_01/
                test_01_output.log
                results/
                    ..
            host_02/
                test_01_output.log
                results/
                    ..
        """
        # dynamic playbook
        playbook = 'cbn_synchronize.yml'

        # local path on disk to save artifacts
        destination = os.path.join(self.datadir, 'artifacts')

        # create artifacts location (if needed)
        if not os.path.exists(destination):
            os.makedirs(destination)

        self.logger.info('Fetching test artifacts @ %s' % destination)

        # settings required by synchronize module
        os.environ['ANSIBLE_LOCAL_TEMP'] = '$HOME/.ansible/tmp'
        os.environ['ANSIBLE_REMOTE_TEMP'] = '$HOME/.ansible/tmp'

        # set extra vars
        extra_vars = copy.deepcopy(self.ans_extra_vars)
        extra_vars['dest'] = destination
        extra_vars['artifacts'] = self.artifacts

        # create dynamic playbook
        self._create_playbook(playbook, SYNCHRONIZE_PLAYBOOK)

        # run playbook
        results = self.ans_controller.run_playbook(
            playbook,
            logger=self.logger,
            extra_vars=extra_vars,
            ans_verbosity=self.ans_verbosity
        )

        # remove dynamic playbook
        os.remove(playbook)

        if results[0] != 0:
            raise CarbonExecuteError('A failure occurred while trying to copy '
                                     'test artifacts.')

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
