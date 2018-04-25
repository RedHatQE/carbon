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
    carbon.controllers

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from collections import namedtuple

from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase

# TODO: future release we should depreciate ansible < 2.4 for python 3 support
try:
    from ansible.inventory import Inventory
    from ansible.vars import VariableManager
except ImportError:
    from ansible.inventory.manager import InventoryManager as Inventory
    from ansible.vars.manager import VariableManager

from .core import CarbonController, CarbonControllerError


class CarbonCallback(CallbackBase):
    """Carbon's custom Ansible callback class. It handles storing all task
    results (as they finish) into one object to be used later for further
    parsing.
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


class AnsibleController(CarbonController):
    """Ansible controller class.

    This is carbons Ansible controller class to drive remote machine
    configuration and management.
    """
    __controller_name__ = 'Ansible'

    def __init__(self, inventory=None):
        """Constructor.

        When the Ansible worker class is instantiated, it will perform the
        following tasks:

        * Initialize required Ansible objects.

        :param inventory: The inventory host file.
        """
        super(AnsibleController, self).__init__()
        self.loader = DataLoader()
        self.callback = CarbonCallback()
        self.ansible_inventory = inventory
        self.inventory = None
        self.variable_manager = None

        # Module options
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

        # Playbook options
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
        """Instantiate the inventory class with the inventory file in-use."""
        try:
            # supports ansible < 2.4
            self.variable_manager = VariableManager()
            self.inventory = Inventory(
                loader=self.loader,
                variable_manager=self.variable_manager,
                host_list=self.ansible_inventory
            )
        except TypeError:
            # supports ansible > 2.4
            self.variable_manager = VariableManager(loader=self.loader)
            self.inventory = Inventory(
                loader=self.loader,
                sources=self.ansible_inventory
            )
        finally:
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
        # Instantiate callback class
        self.callback = CarbonCallback()

        # Set inventory file
        self.set_inventory()

        # Define ansible options
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

        # Load the play
        play = Play().load(
            play_source,
            variable_manager=self.variable_manager,
            loader=self.loader
        )

        # Run the tasks
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=options,
                passwords={},
                stdout_callback=self.callback
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        return dict(status=result, callback=self.callback)

    def run_playbook(self, playbook, extra_vars=None, become=False,
                     become_method="sudo", become_user="root",
                     remote_user="root", private_key_file=None):
        """Run an Ansible playbook.

        :param playbook: Playbook to call
        :param extra_vars: Additional variables for playbook
        :param become: Whether to run as sudoer
        :param become_method: Method to use for become
        :param become_user: User to become to run playbook call
        :param remote_user: Connect as this user
        :param private_key_file: SSH private key for authentication
        :return: A dict of Ansible return code and callback object
        """
        # Instantiate callback class
        self.callback = CarbonCallback()

        # Set inventory file
        self.set_inventory()

        # Define ansible options
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

        # Set additional variables for use by playbook
        if extra_vars is not None:
            self.variable_manager.extra_vars = extra_vars

        # Instantiate playbook executor object
        runner = PlaybookExecutor(
            playbooks=[playbook],
            inventory=self.inventory,
            variable_manager=self.variable_manager,
            loader=self.loader,
            options=options,
            passwords={}
        )

        # Set stdout_callback to use custom callback class
        runner._tqm._stdout_callback = self.callback

        # Run playbook
        result = runner.run()

        return dict(status=result, callback=self.callback)

    def results_analyzer(self, status):
        """Results analyzer.

        This is a simple method that performs results analzying. It is good to
        use when you need to log the standard error/output based on the
        return code from ansible call.

        :param status: Status code of ansible call
        """
        for item in self.callback.contacted:
            if status != 0:
                if 'stderr' in item['results']:
                    self.logger.info('Standard error:')
                    self.logger.error(item['results']['stderr'])
            if 'stdout' in item['results']:
                self.logger.debug('Standard output:')
                self.logger.debug(item['results']['stdout'])
            if 'msg' in item['results']:
                self.logger.info('Message:')
                self.logger.info(item['results']['msg'])
