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
from collections import namedtuple
from os import remove
from os.path import isfile
from uuid import uuid4
from shutil import copyfile
import logging

from ansible.cli.galaxy import GalaxyCLI
from ansible.config.manager import ConfigManager
from ansible.errors import AnsibleError
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager

from .._compat import RawConfigParser, urlparse, string_types
from ..core import CarbonOrchestrator, CarbonOrchestratorError, LoggerMixin
from ..helpers import file_mgmt, ssh_retry, exec_local_cmd_pipe


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

    def set_inventory(self):
        """Create the ansible inventory object with the supplied inventory."""
        self.variable_manager = VariableManager(loader=self.loader)
        self.inventory = InventoryManager(
            loader=self.loader,
            sources=self.ansible_inventory
        )
        self.variable_manager.set_inventory(self.inventory)

    @ssh_retry
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

    @ssh_retry
    def run_playbook(self, playbook, logger, extra_vars=None, run_options=None,
                     ans_verbosity=None):
        """Run an Ansible playbook.

        :param playbook: Playbook to call
        :type playbook: str
        :param extra_vars: Additional variables for playbook
        :type extra_vars: dict
        :param run_options: playbook run options
        :type run_options: dict
        :param ans_verbosity: ansible verbosity settings
        :type ans_verbosity: str
        :return: A tuple (rc, stdout, sterr)
        """

        playbook_call = "ansible-playbook -i %s %s" % \
                        (self.ansible_inventory, playbook)
        if extra_vars is not None:
            for key in extra_vars:
                if not isinstance(extra_vars[key], string_types):
                    extra_var_dict = {}
                    extra_var_dict[key] = extra_vars[key]
                    playbook_call += ' -e "%s" '% (extra_var_dict)
                else:
                    playbook_call += " -e %s=%s" % (key, extra_vars[key])

        if run_options:
            for key in run_options:
                if key == "remote_user":
                    playbook_call += " --user %s" % run_options[key]
                elif key == "become":
                    if run_options[key]:
                        playbook_call += " --%s" % key
                elif key == "tags":
                    taglist = ','.join(run_options[key])
                    playbook_call += " --tags %s" % taglist
                else:
                    playbook_call += " --%s %s" % (key.replace('_','-'), run_options[key])

        if ans_verbosity:
            playbook_call += " -v%s" % ans_verbosity

        output = exec_local_cmd_pipe(playbook_call, logger)
        return output


class Inventory(object):
    """Inventory.

    This class primary responsibility is handling creating/deleting the
    ansible inventory for the carbon ansible action.
    """

    def __init__(self, hosts, all_hosts, data_dir):
        """Constructor.

        :param hosts: list of hosts to create the inventory file
        :type hosts: list
        :param all_hosts: list of all hosts in the given scenario
        :type all_hosts: list
        :param data_dir: data directory where the inventory directory resides
        :type data_dir: str
        """
        self.hosts = hosts
        self.all_hosts = all_hosts

        # create the inventory directory where all inventory files are stored
        self._inventory_dir = os.path.join(data_dir, 'inventory')

        # create a master inventory for all hosts within the scenario.
        self._master_inventory = os.path.join(
            self._inventory_dir, 'master-%s' % uuid4())

        # create a unique inventory for the actions hosts
        self._unique_inventory = os.path.join(
            self._inventory_dir, 'unique-%s' % uuid4())

        # Each action inventory will have a default group. This group will be
        # the one given to ansible controller object. Within this group is all
        # the hosts to have the given action run against. Nice feature is with
        # the group having potentially multiple hosts. Ansible will run that
        # action against all the hosts in the group concurrently.
        self._group = 'hosts'

    @property
    def master_inventory(self):
        """Return the master inventory."""
        return self._master_inventory

    @property
    def unique_inventory(self):
        """Return the unique inventory."""
        return self._unique_inventory

    @property
    def inventory_dir(self):
        """Return the ansible inventory directory."""
        return self._inventory_dir

    @property
    def group(self):
        """Return the ansible base group name."""
        return self._group

    def _create_inventory_dir(self):
        """Create the ansible inventory directory."""
        if not os.path.isdir(self.inventory_dir):
            os.makedirs(self.inventory_dir)

    def _create_master(self):
        """Create the master ansible inventory.

        This method will create a master inventory which contains all the
        hosts in the given scenario. Each host will have a group/group:vars.
        """
        # create parser object, raw config parser allows keys with no values
        config = RawConfigParser(allow_no_value=True)

        for host in self.all_hosts:
            section = host.name
            section_vars = '%s:vars' % section

            if host.role:
                host_section = host.role + ":children"
                if host_section in config.sections():
                    config.set(host_section, host.name)
                else:
                    config.add_section(host_section)
                    config.set(host_section, host.name)

            # create section(s)
            for item in [section, section_vars]:
                config.add_section(item)

            # add alias to resolve lack of dns
            config.set(section, host.name)

            # add host vars
            for k, v in host.ansible_params.items():
                if k in ['ansible_ssh_private_key_file']:
                    v = os.path.join(getattr(host, 'workspace'), v)
                config.set(section_vars, k, v)

            # add host ip address reference for the alias defined above
            if isinstance(host.ip_address, list):
                for item in host.ip_address:
                    config.set(section_vars, 'ansible_host', item)
            elif isinstance(host.ip_address, str):
                config.set(section_vars, 'ansible_host', host.ip_address)

        # write the inventory
        with open(self.master_inventory, 'w') as f:
            config.write(f)

    def _create_unique(self):
        """Create the unique ansible inventory.

        This method will create a unique inventory which contains placeholders
        for all hosts in the scenario. Along with a child group containing
        all the hosts for the action to run on.
        """
        # create parser object, raw config parser allows keys with no values
        config = RawConfigParser(allow_no_value=True)
        config.add_section(self.group)

        # add place holders for all hosts
        for host in self.all_hosts:
            config.add_section(host.name)

        # add specific hosts to the group to run the action against
        for host in self.hosts:
            config.set(self.group, host.name)

        # write the inventory
        with open(self.unique_inventory, 'w') as f:
            config.write(f)

    def create(self):
        """Create the inventory."""
        self._create_inventory_dir()
        self._create_master()
        self._create_unique()

    def delete(self):
        """Delete the ansible inventory file if it exists."""
        for item in [self.master_inventory, self.unique_inventory]:
            if isfile(item):
                remove(item)


class Role(LoggerMixin):
    """
    This class handles requests given to carbon to make use of ansible roles
    defined by its input.
    """

    def __init__(self, action):
        """Constructor.

        Creates galaxy cli object and sets its default optons.

        :param action: galaxy action to process
        :type action: str
        """
        self.cli = GalaxyCLI(args=[action])
        self.cli.parse()

    @staticmethod
    def _update_options(default_options, user_options):
        """Combine the command options.

        :param default_options: default options
        :type default_options: dict
        :param user_options: user supplied options
        :type user_options: dict
        :return: command options
        :rtype: dict
        """
        if user_options:
            default_options.update(user_options)
        return default_options

    def _set_galaxy_cli_options(self, options):
        """Set galaxy cli options.

        :param options: command options to set
        :type options: dict
        """
        for key, value in options.items():
            setattr(self.cli.options, key, value)

    def install(self, role=None, role_file=None, options=None):
        """Install ansible roles either by role name or role file.

        :param role: role name
        :type role: str
        :param role_file: role requirements file
        :type role_file: str
        :param options: galaxy install command options
        :type options: dict
        :return: 0 - pass | 1 - fail
        :rtype: int
        """
        # default options
        _options = dict(force=False)

        # set galaxy cli command options
        self._set_galaxy_cli_options(self._update_options(_options, options))

        # set role type options
        if role_file:
            self._set_galaxy_cli_options(dict(role_file=role_file))
        elif role:
            self.cli.args = [role]
        else:
            self.logger.error('No input given. Unable to install role.')
            return 1

        # install ansible role
        try:
            self.cli.run()
        except AnsibleError as ex:
            self.logger.error(ex)
            return 1

        return 0

    def remove(self, role=None, role_file=None, options=None):
        """Remove installed ansible roles by role name or role file.

        :param role: role name
        :type role: str
        :param role_file: role requirements file
        :type role_file: str
        :param options: galaxy install command options
        :type options: dict
        :return: 0 - pass | 1 - fail
        :rtype: int
        """
        # default options
        _options = dict()

        # set galaxy cli command options
        self._set_galaxy_cli_options(self._update_options(_options, options))

        if role_file:
            # locate the role file
            if not os.path.isfile(role_file):
                self.logger.error('Unable to locate role file: %s' % role_file)
                return 1

            # load role file
            for item in file_mgmt('r', role_file):
                if 'name' in item:
                    self.cli.args.append(item['name'])
                    continue

                # determine src type (galaxy role vs external site)
                parsed = urlparse(item['src'])
                if parsed.scheme:
                    # non galaxy role
                    self.cli.args.append(os.path.split(parsed.path)[-1])
                else:
                    # galaxy role
                    self.cli.args.append(parsed.path)
        elif role:
            self.cli.args = [role]
        else:
            self.logger.error('No input given. Unable to remove role.')
            return 1

        # remove installed ansible roles
        self.cli.run()

        return 0


class AnsibleOrchestrator(CarbonOrchestrator):
    """Ansible orchestrator.

    This class primary responsibility is for processing carbon actions.
    These actions for the ansible orchestrator could be in the form of a
    playbook or module call.
    """
    __orchestrator_name__ = 'ansible'
    _action_abs = None

    _optional_parameters = (
        'options',
        'galaxy_options'
    )

    user_run_vals = ["become", "become_method", "become_user", "remote_user",
                     "connection", "forks"]

    def __init__(self, package):
        """Constructor.

        :param package: action resource
        :type package: object
        """
        super(AnsibleOrchestrator, self).__init__()

        # set attributes
        self._action = getattr(package, 'name')
        self._hosts = getattr(package, 'hosts')
        self.options = getattr(package, '%s_options' % self.name)
        self.galaxy_options = getattr(package, '%s_galaxy_options' % self.name)
        self.config = getattr(package, 'config')
        self.all_hosts = getattr(package, 'all_hosts')
        self.workspace = self.config['WORKSPACE']

        # create inventory object for create/delete inventory file
        self.inv = Inventory(
            self.hosts,
            self.all_hosts,
            data_dir=self.config['DATA_FOLDER']
        )

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

    def find_playbook(self):
        """fn to see if a playbook exists and to set the path of it
        """
        # TODO: this should be moved to validate task
        # determine the directory to traverse through
        path = self.workspace
        _path = os.path.dirname(self.action)
        if not _path == "":
            path = os.path.join(path, _path)

        for item in os.listdir(path):
            if item in self.action:
                self.action_abs = os.path.join(path, item)
                self.logger.info(
                    'Playbook found for action: %s @ %s' %
                    (self.action, self.action_abs)
                )
                return
        self.logger.warning(
            'Playbook not found for action: %s @ '
            '%s' % (self.action, path)
        )

        if self.action_abs is None:
            raise CarbonOrchestratorError(
                'Unable to locate action %s for ansible orchestrator. '
                'Cannot continue!'
            )

    def download_roles(self):
        """Download ansible roles defined for the given action."""
        flag = 0

        if self.galaxy_options is None:
            return

        if 'role_file' in self.galaxy_options:
            flag += 1

            f = os.path.join(self.config['WORKSPACE'],
                             self.galaxy_options['role_file'])
            self.logger.info('Installing roles using req. file: %s' % f)

            role = Role('install')
            rc = role.install(role_file=f)

            if rc != 0:
                raise CarbonOrchestratorError(
                    'A problem occurred while installing roles using req. file'
                    ' %s' % f)
            self.logger.info('Roles installed successfully from: %s!' % f)

        if 'roles' in self.galaxy_options:
            if flag >= 1:
                self.logger.warning('FYI roles were already installed using a'
                                    ' requirements file. Problems may occur.')

            for item in self.galaxy_options['roles']:
                role = Role('install')
                rc = role.install(role=item)

                if rc != 0:
                    raise CarbonOrchestratorError(
                        'A problem occurred while installing role: %s' % item
                    )
                self.logger.info('Role: %s successfully installed!' % item)

    def get_default_config(self, key=None):
        """getting the default configuration defined by ansible.cfg
        (Uses default values if there is no ansible.cfg).

        :param key: get a value of a specific key of the ansible.cfg file
        :type key: str

        :return: key/values of the default ansible configuration or
                 a specifc value of the config
        :rtype: dict if key not defined or string if defined
        """
        returndict = {}
        acm = ConfigManager()
        a_settings = acm.data.get_settings()
        if key:
            for setting in a_settings:
                if setting.name == key:
                    return setting.value
            return None
        else:
            for setting in a_settings:
                if setting.name == "CONFIG_FILE":
                    self.logger.debug("Using %s for default configuration" % setting.value)
                elif setting.name == "DEFAULT_BECOME":
                    returndict["become"] = setting.value
                elif setting.name == "DEFAULT_BECOME_METHOD":
                    returndict["become_method"] = setting.value
                elif setting.name == "DEFAULT_BECOME_USER":
                    returndict["become_user"] = setting.value
                elif setting.name == "DEFAULT_REMOTE_USER":
                    returndict["remote_user"] = setting.value
                elif setting.name == "DEFAULT_FORKS":
                    returndict["forks"] = setting.value
                elif setting.name == 'DEFAULT_TRANSPORT':
                    returndict["connection"] = setting.value
            return returndict

    def alog_update(self):
        """move ansible logs to data folder as needed
        """
        ans_logfile = self.get_default_config(key="DEFAULT_LOG_PATH")
        if ans_logfile:
            dest = os.path.join(self.config['DATA_FOLDER'], 'logs', "ansible.log")
            # if user wishes to keep the ansible log copy the log file
            if os.path.isfile(dest) and not self.config["ANSIBLE_LOG_REMOVE"]:
                copyfile(ans_logfile, dest)
            # if user wants to delete the log file (default)
            elif os.path.isfile(dest):
                with open(dest, "a") as destfile:
                    with open(ans_logfile) as logfile:
                        for line in logfile:
                            destfile.write(line)
            else:
                copyfile(ans_logfile, dest)
            # remove ansible log (default)
            if os.path.isfile(ans_logfile) and self.config["ANSIBLE_LOG_REMOVE"]:
                os.remove(ans_logfile)
            self.logger.debug("ansible logging moved to: %s" % dest)

    def run(self):
        """Run.

        This method handles the bulk work for the ansible orchestrator class.
        Here you will see every required step for processing a carbon ansible
        action. Please see the comments below for step by step details.
        """
        # For the first implementation or ansible orchestrator, we are focused
        # solely on playbooks. Since each action's name key defines the
        # item to run, we need to verify it is available.
        self.find_playbook()

        # lets create the ansible inventory file to run the given action on
        # its associated hosts
        self.inv.create()

        # download ansible roles (if applicable)
        self.download_roles()

        # create an ansible controller object
        obj = AnsibleController(self.inv.inventory_dir)

        # configure playbook variables
        extra_vars = dict(hosts=self.inv.group)

        if 'extra_vars' in self.options and self.options['extra_vars']:
            extra_vars.update(self.options['extra_vars'])

        self.logger.info('Executing action: %s.' % self.action)

        run_options = {}

        if "tags" in self.options and self.options["tags"]:
            run_options["tags"] = self.options["tags"]

        # override ansible options (user passed in vals for specific action)
        for val in self.user_run_vals:
            if val in self.options and self.options[val]:
                run_options[val] = self.options[val]

        self.logger.debug("Ansible options used: " + str(run_options))

        ans_verbosity = None

        log_level = self.logger.getEffectiveLevel()
        if log_level == logging.DEBUG:
            ans_verbosity = "vvvv"

        if "ANSIBLE_VERBOSITY" in self.config and \
                self.config["ANSIBLE_VERBOSITY"]:
            ans_verbosity = self.config["ANSIBLE_VERBOSITY"]

        results = obj.run_playbook(
            self.action_abs,
            extra_vars=extra_vars,
            run_options=run_options,
            ans_verbosity=ans_verbosity,
            logger=self.logger
        )

        self.logger.info('Finished action: %s execution.' % self.action)
        self.logger.info('Status => %s.' % results[0])

        # get ansible logs as needed
        self.alog_update()

        # Since we reached here, we are done processing the action. Lets go
        # ahead and delete the inventory for this action run.
        self.inv.delete()

        # raise an exception if the ansible action failed
        if results[0] != 0:
            raise CarbonOrchestratorError(
                'Ansible action did not return a valid return code!'
            )
