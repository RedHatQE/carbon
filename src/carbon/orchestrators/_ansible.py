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
    carbon.orchestrators._ansible

    Carbon's ansible orchestrator module which contains all the necessary
    classes to process ansible actions defined within the scenario descriptor
    file.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import os
import time
from collections import namedtuple
from os import remove
from os.path import isfile
from uuid import uuid4

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager

from .._compat import RawConfigParser
from ..core import CarbonOrchestrator, CarbonOrchestratorError


class CarbonCallback(CallbackBase):
    """Carbon callback.

    This class primary responsibility is to handle building the callback data
    from an ansible execution. This is a base callback class that can be
    inherited from/expanded. Ansible controller objects can benefit from using
    a custom callback class for easier parsing of the results after execution.
    """

    def __init__(self):
        """Constructor."""
        super(CarbonCallback, self).__init__()
        self.contacted = []
        self.unreachable = False

    def v2_runner_on_ok(self, result):
        """Store ok results."""
        CallbackBase.v2_runner_on_ok(self, result)
        self.contacted.append(
            {
                'host': result._host.get_name(),
                'success': True,
                'results': result._result
            }
        )

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Store failed results."""
        CallbackBase.v2_runner_on_failed(
            self, result, ignore_errors=ignore_errors)
        self.contacted.append(
            {
                'host': result._host.get_name(),
                'success': False,
                'results': result._result
            }
        )

    def v2_runner_on_unreachable(self, result):
        """Store unreachable results."""
        CallbackBase.v2_runner_on_unreachable(self, result)
        self.unreachable = True


class AnsibleController(object):
    """Ansible controller.

    The primary responsibility is for driving the execution of either modules
    or playbooks to configure/manage remote machines.
    """

    def __init__(self, inventory):
        """Constructor.

        Primarily used for initializing attributes used by module/playbook
        execution.

        :param inventory: inventory file
        """
        self.loader = DataLoader()
        self.callback = CarbonCallback()
        self.ansible_inventory = inventory
        self.inventory = None
        self.variable_manager = None

        # module options
        self.module_options = namedtuple(
            'Options', ['connection',
                        'module_path',
                        'forks',
                        'become',
                        'become_method',
                        'become_user',
                        'check',
                        'remote_user',
                        'private_key_file',
                        'diff']
        )

        # playbook options
        self.playbook_options = namedtuple(
            'Options', ['connection',
                        'module_path',
                        'forks',
                        'become',
                        'become_method',
                        'become_user',
                        'check',
                        'listtags',
                        'listtasks',
                        'listhosts',
                        'syntax',
                        'remote_user',
                        'private_key_file',
                        'diff']
        )

    def set_inventory(self):
        """Create the ansible inventory object with the supplied inventory."""
        self.variable_manager = VariableManager(loader=self.loader)
        self.inventory = InventoryManager(
            loader=self.loader,
            sources=self.ansible_inventory
        )
        self.variable_manager.set_inventory(self.inventory)

    def run_module(self, play_source, remote_user="root", become=False,
                   become_method="sudo", become_user="root",
                   private_key_file=None):
        """Run an Ansible module.

        Example play source:
        dict(
            name="Ansible Play",
            hosts=192.168.1.1,
            gather_facts='no',
            tasks=[
                dict(action=dict(module='ping'), register='shell_out')
            ]
        )

        :param play_source: Play to be run.
        :param remote_user: Connect as this user.
        :param become: Whether to run as sudoer.
        :param become_method: Method to use for become.
        :param become_user: User to become.
        :param private_key_file: SSH private key for authentication.
        :return: A dict of Ansible return code and callback object
        """
        # instantiate callback class
        self.callback = CarbonCallback()

        # set inventory file
        self.set_inventory()

        # define ansible options
        options = self.module_options(
            connection='smart',
            module_path='',
            forks=100,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=False,
            remote_user=remote_user,
            private_key_file=private_key_file,
            diff=False
        )

        # load the play
        play = Play().load(
            play_source,
            variable_manager=self.variable_manager,
            loader=self.loader
        )

        # run the tasks
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=options,
                passwords={}
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        return dict(status=result, callback=self.callback)

    def run_playbook(self, playbook, extra_vars=None, become=False,
                     become_method="sudo", become_user="root",
                     remote_user="root", private_key_file=None,
                     default_callback=False):
        """Run an Ansible playbook.

        :param playbook: Playbook to call
        :param extra_vars: Additional variables for playbook
        :param become: Whether to run as sudoer
        :param become_method: Method to use for become
        :param become_user: User to become to run playbook call
        :param remote_user: Connect as this user
        :param private_key_file: SSH private key for authentication
        :param default_callback: enable default callback
        :return: A dict of Ansible return code and callback object
        """
        # instantiate callback class
        self.callback = CarbonCallback()

        # set inventory file
        self.set_inventory()

        # define ansible options
        options = self.playbook_options(
            connection='smart',
            module_path='',
            forks=100,
            become=become,
            become_method=become_method,
            become_user=become_user,
            check=False,
            listtags=False,
            listtasks=False,
            listhosts=False,
            syntax=False,
            remote_user=remote_user,
            private_key_file=private_key_file,
            diff=False
        )

        # set additional variables for use by playbook
        if extra_vars is not None:
            self.variable_manager.extra_vars = extra_vars

        # instantiate playbook executor object
        runner = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=options,
            passwords={}
        )

        # set ansible to use the custom callback class
        if default_callback is False:
            runner._tqm._stdout_callback = self.callback

        # run playbook
        result = runner.run()

        return dict(status=result, callback=self.callback)


class Inventory(object):
    """Inventory.

    This class primary responsibility is handling creating/deleting the
    ansible inventory for the carbon ansible action.
    """

    def __init__(self, hosts, asset_params):
        """Constructor.

        :param hosts: list of hosts to create the inventory file
        :param asset_params: tuple of orchestrator assets
        """
        self.hosts = hosts
        self.asset_params = asset_params

        # create a unique inventory filename for the given action
        # default this file will be deleted, maybe in future it can be saved
        self._inventory = 'inv-%s' % uuid4()

        # Each action inventory will have a default group. This group will be
        # the one given to ansible controller object. Within this group is all
        # the hosts to have the given action run against. Nice feature is with
        # the group having potentially multiple hosts. Ansible will run that
        # action against all the hosts in the group concurrently.
        self._group = 'hosts:children'

    @property
    def inventory(self):
        """Return the ansible inventory file."""
        return self._inventory

    @property
    def group(self):
        """Return the ansible base group name."""
        return self._group

    def create(self):
        """Create the ansible inventory file.

        This will create a section/section:vars for each host associated to
        the carbon ansible action. Once all hosts have a created section, the
        host sections will be added to the default group.
        """
        # create parser object, raw config parser allows keys with no values
        config = RawConfigParser(allow_no_value=True)

        # create a base group for all hosts
        config.add_section(self.group)

        # now lets create individual host sections
        for host in self.hosts:
            section = host.name
            section_vars = '%s:vars' % section

            # create section(s)
            config.add_section(section)
            config.add_section(section_vars)

            # add host
            if isinstance(host.ip_address, list):
                for item in host.ip_address:
                    config.set(section, item)
            elif isinstance(host.ip_address, str):
                config.set(section, host.ip_address)

            # add host vars
            for k, v in host.ansible_params.items():
                if k in self.asset_params:
                    v = os.path.join(host.data_folder(), 'assets', v)
                config.set(section_vars, k, v)

            # add host to group
            config.set(self.group, section)

        # write the inventory
        with open(self.inventory, 'w') as f:
            config.write(f)

    def delete(self):
        """Delete the ansible inventory file if it exists."""
        if isfile(self.inventory):
            remove(self.inventory)


class AnsibleOrchestrator(CarbonOrchestrator):
    """Ansible orchestrator.

    This class primary responsibility is for processing carbon actions.
    These actions for the ansible orchestrator could be in the form of a
    playbook or module call.
    """
    __orchestrator_name__ = 'ansible'
    _action_abs = None

    _assets_parameters = (
        'ansible_ssh_private_key_file',
    )

    def __init__(self, action, hosts, **kwargs):
        """Constructor.

        :param action: action to be executed (module/playbook)
        :param hosts: action runs against these hosts
        :param kwargs: action parameters
        """
        super(AnsibleOrchestrator, self).__init__(action, hosts, **kwargs)

        # create inventory object for create/delete inventory file
        self.inv = Inventory(hosts, self._assets_parameters)

    @property
    def action_abs(self):
        """Return the action absolute path."""
        return self._action_abs

    @action_abs.setter
    def action_abs(self, value):
        """Set the action absolute path."""
        self._action_abs = value

    def validate(self):
        """Validate.

        TBD..
        """
        raise NotImplementedError

    def _find_playbook(self, path, name):
        for item in os.listdir(path):
            filename, extension = os.path.splitext(item)
            if filename == self.action and extension in ['.yml', '.yaml']:
                self.action_abs = os.path.join(path, item)
                self.logger.info(
                    'Playbook found within %s defined directory for action: %s'
                    ' @ %s' % (name, self.action, self.action_abs)
                )
                return
        self.logger.warning(
            'Playbook not found within %s defined directory for action: %s @ '
            '%s' % (name, self.action, path)
        )

    def _locate_action(self, name='common'):
        """Locate the action's playbook. (child)

        This method will attempt to find the action playbook at two
        directories: 1. common directory (current working directory)
        2. user defined directory.

        :param name: type of location for orchestrator files
        """
        # placeholder
        path = str

        # determine the file path
        if name == 'common':
            path = os.path.join(os.getcwd(), 'orchestrate', self.name)
        elif name == 'user':
            path = os.path.join(getattr(self, 'config')['DATA_FOLDER'],
                                'assets', self.name)

        # return if the directory does not exist
        if not os.path.isdir(path):
            self.logger.warn('Unable to locate a %s ansible orchestrator '
                             'scripts directory.' % name)
            return

        # find the playbook for the action under the given path
        self._find_playbook(path, name)

    def locate_action(self):
        """Locate the action's playbook. (parent).

        See _locate_action doc string for more details.
        """
        # locate the action playbook in common directory
        self._locate_action('common')

        # locate the action playbook in the user defined directory
        self._locate_action('user')

        # quit if no playbook was found for the given action
        if self.action_abs is None:
            raise CarbonOrchestratorError(
                'Unable to locate action %s for ansible orchestrator. '
                'Cannot continue!'
            )

    def run(self):
        """Run.

        This method handles the bulk work for the ansible orchestrator class.
        Here you will see every required step for processing a carbon ansible
        action. Please see the comments below for step by step details.
        """
        # For the first implementation or ansible orchestrator, we are focused
        # solely on playbooks. Since each action's name key defines the
        # item to run. We need to determine if the item is a common one
        # supplied by carbon or custom to the scenario run by carbon.
        self.locate_action()

        # lets create the ansible inventory file to run the given action on
        # its associated hosts
        self.inv.create()

        # now that we have the absolute path and all information regarding the
        # action to execute, lets go ahead and begin..

        # create an ansible controller object
        obj = AnsibleController(self.inv.inventory)

        # setup variables
        extra_vars = dict(hosts=self.inv.group)
        extra_vars.update(getattr(self, 'vars'))

        self.logger.info('Executing action: %s.' % self.action)

        # delay for 5 seconds before processing the action
        # it is observed that hosts are unreachable proceeding right from
        # provision task.
        # RFE: remove this and maybe add a retry?
        time.sleep(5)

        results = obj.run_playbook(
            self.action_abs,
            extra_vars=extra_vars,
            default_callback=True
        )

        self.logger.info('Finished action: %s execution.' % self.action)
        self.logger.info('Status => %s.' % results['status'])

        # Since we reached here, we are done processing the action. Lets go
        # ahead and delete the inventory for this action run.
        self.inv.delete()

        # raise an exception if the ansible action failed
        if results['status'] != 0:
            raise CarbonOrchestratorError(
                'Ansible action did not return a valid return code!'
            )
