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
from ..core import CarbonOrchestrator
from ..exceptions import CarbonOrchestratorError, AnsibleServiceError
from ..helpers import DataInjector
from ..ansible_helpers import AnsibleService


class AnsibleOrchestrator(CarbonOrchestrator):
    """Ansible orchestrator.

    This class primary responsibility is for processing carbon actions.
    These actions for the ansible orchestrator could be in the form of a
    playbook or module call.
    """
    __orchestrator_name__ = 'ansible'

    _optional_parameters = (
        'options',
        'galaxy_options',
        'script',
        'playbook',
        'shell'
    )

    _action_types = [
        'ansible_script',
        'ansible_playbook',
        'ansible_shell'
    ]

    def __init__(self, package):
        """Constructor.

        :param package: action resource
        :type package: object
        """
        super(AnsibleOrchestrator, self).__init__()

        self.action_name = getattr(package, 'name')
        self._hosts = getattr(package, 'hosts')
        self.desc = getattr(package, 'description')
        self.options = getattr(package, '%s_options' % self.name)
        self.galaxy_options = getattr(package, '%s_galaxy_options' % self.name)
        self.config = getattr(package, 'config')
        self.all_hosts = getattr(package, 'all_hosts')
        self.workspace = self.config['WORKSPACE']
        self.playbook = getattr(package, '%s_playbook' % self.name, None)
        self.script = getattr(package, '%s_script' % self.name, None)
        self.shell = getattr(package, '%s_shell' % self.name, None)

        # calling the method to do a backward compatibility check in case user is defining name field as a path for
        # script or playbook
        # TODO delete this if we want to remove backward compatibility for later releases
        self.backwards_compat_check()

        # saving package to set status later
        self.package = package

        # ansible service object
        self.ans_service = AnsibleService(self.config, self.hosts, self.all_hosts, self.options, self.galaxy_options)

        # setup injector
        self.injector = DataInjector(self.all_hosts)

    def backwards_compat_check(self):
        """ This method does the check if name field is a script/playbook path or name of the orchestrator task by
            checking is '/' i spresent in the string.
            If it is a path then it checks if ansible_script field is a boolean and is True . If so
            a new dictionary is created with key=name and the value= script path. This is then assigned to
            ansible_script.
            If the ansible_script is not present then it is understood that the path belongs to a playbook.
             a new dictionary is created with key=name and the value= playbook path. This is then assigned to
            ansible_playbook.
            """

        if os.sep in self.action_name:
            self.logger.warning('Using name field to provide ansible_script/ansible_playbook path')

            self.logger.debug('Joining current workspace %s to the ansible_script/playbook path %s'
                              % (self.workspace, self.action_name))
            new_item = {'name': os.path.join(self.workspace, self.action_name)}

            self.logger.debug('Converting ansible_script/playbook path to dictionary %s' % new_item)
            if isinstance(self.script, bool) and self.script:
                self.script = new_item
            elif not self.script:
                self.playbook = new_item
            else:
                raise CarbonOrchestratorError('Error in defining the orchestrate name/ansible_script/ansible_playbook'
                                              ' fields')

    def validate(self):
        """Validate that script/playbook path is valid and exists."""

        if self.script:
            if os.path.exists(self.script.get('name').split(' ', 1)[0]):
                self.logger.debug('Found Action script %s' % self.script.get('name'))
            else:
                raise CarbonOrchestratorError('Cannot find Action script %s' % self.script.get('name'))
        elif self.playbook:
            if os.path.exists(self.playbook.get('name').split(' ', 1)[0]):
                self.logger.debug('Found Action playbook %s' % self.playbook.get('name'))
            else:
                raise CarbonOrchestratorError('Cannot find Action playbook %s' % self.playbook.get('name'))

    def __playbook__(self):
        self.logger.info('Executing playbook:')
        results = self.ans_service.run_playbook(self.playbook)
        if results[0] != 0:
            raise CarbonOrchestratorError('Playbook %s failed to run successfully!' % self.playbook['name'])
        else:
            self.logger.info('Successfully completed playbook : %s' % self.playbook['name'])

    def __script__(self):
        self.logger.info('Executing script:')

        result = self.ans_service.run_script_playbook(self.script)
        if result['rc'] != 0:
            raise CarbonOrchestratorError('Script %s failed. Host=%s rc=%d Error: %s'
                                          % (self.script['name'], result['host'], result['rc'], result['err']))
        else:
            self.logger.info('Successfully completed script : %s' % self.script['name'])

    def __shell__(self):
        self.logger.info('Executing shell command:')
        result = self.ans_service.run_shell_playbook(self.shell)
        if result['rc'] != 0:
            raise CarbonOrchestratorError('Command %s failed. Host=%s rc=%d Error: %s'
                                           % (self.shell['command'], result['host'], result['rc'], result['err']))
        else:
            self.logger.info('Successfully completed command : %s' % self.shell['command'])

    def run(self):
        """Run method for orchestrator.
        """
        # Orchestrate supports only one action_types( playbook, script or shell) per task
        # if more than one action types are declared then the first action_type found will be executed

        flag = 0
        for item in ['playbook', 'script', 'shell']:
            # Orchestrate supports only one action_types( playbook, script or shell) per task
            # if more than one action types are declared then the first action_type found will be executed
            if getattr(self, item):
                flag += 1
                # Download ansible roles (if applicable)
                if flag == 1:
                    try:
                        self.ans_service.download_roles()
                    except (CarbonOrchestratorError, AnsibleServiceError):
                        if 'retry' in self.galaxy_options and self.galaxy_options['retry']:
                            self.logger.Info("Download failed.  Sleeping 5 seconds and \
                                              trying again")
                            time.sleep(5)
                            self.ans_service.download_roles()

                    try:
                        getattr(self, '__%s__' % item)()
                    except (CarbonOrchestratorError, AnsibleServiceError) as e:
                        setattr(self.package, 'status', 1)
                        raise CarbonOrchestratorError("Orchestration failed : %s" % e.message)
                    finally:
                        # get ansible logs as needed
                        self.ans_service.alog_update()
                else:
                    self.logger.warning('Found more than one action types (ansible_playbook, ansible_script ,'
                                        'ansible_shell )in the orchestrate task, only the first found'
                                        ' action type was executed, the rest are skipped.')
                    break

        # If every script/playbook/shell command within the each orchestrate has passed, mark that task as
        # successful with status 0
        setattr(self.package, 'status', 0)
        self.logger.info('Completed orchestrate action: %s.' % self.action_name)
