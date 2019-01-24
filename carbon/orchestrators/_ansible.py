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

import logging
import os
from collections import namedtuple
from shutil import copyfile
from uuid import uuid4

from ansible.config.manager import ConfigManager
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager

from .._compat import RawConfigParser, string_types
from ..core import CarbonOrchestrator, LoggerMixin
from ..exceptions import CarbonOrchestratorError
from ..helpers import ssh_retry, exec_local_cmd_pipe, is_host_localhost, get_ans_verbosity


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
    def run_module(self, module, logger, script=None, run_options={},
                   extra_args=None, extra_vars=None, ans_verbosity=None):
        """

        :param module: Name of the ansible module to run.
        :type module: str
        :param logger: Logger object.
        :type logger: logger object
        :param script: Absolute path a script, if using the script module.
        :type script: str
        :param run_options: additional ansible run options
        :type run_options: dict
        :param extra_args: module arguments
        :type extra_args: str
        :param extra_vars: used to determine where to run the module against
        :type extra_vars: dict
        :param ans_verbosity: verbosity to use for the ansible call.
        :type ans_verbosity: str
        :return: A tuple (rc, sterr)
        """

        if "localhost" in extra_vars and extra_vars["localhost"]:
            module_call = "ansible localhost -m %s" % (module)
        else:
            module_call = "ansible -i %s %s -m %s" % \
                          (self.ansible_inventory, extra_vars["hosts"], module)

        # add extra arguments
        if module == "script" or module == "shell":
            if extra_args:
                module_call += " -a '%s %s'" % (script, extra_args)
            else:
                module_call += " -a '%s'" % script
        elif extra_args:
            module_call += " -a '%s'" % extra_args

        if run_options:
            for key in run_options:
                if key == "remote_user":
                    module_call += " --user %s" % run_options[key]
                elif key == "become":
                    if run_options[key]:
                        module_call += " --%s" % key
                elif key == "tags":
                    taglist = ','.join(run_options[key])
                    module_call += " --tags %s" % taglist
                else:
                    module_call += " --%s %s" % (key.replace('_', '-'), run_options[key])

        if ans_verbosity:
            module_call += " -%s" % ans_verbosity

        # Set the connection if localhost
        if "localhost" in extra_vars and extra_vars["localhost"]:
            module_call += " -c local"

        logger.debug(module_call)
        output = exec_local_cmd_pipe(module_call, logger)
        return output

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
        :return: A tuple (rc, sterr)
        """

        playbook_call = "ansible-playbook -i %s %s" % \
                        (self.ansible_inventory, playbook)
        if extra_vars is not None:
            for key in extra_vars:
                if not isinstance(extra_vars[key], string_types):
                    extra_var_dict = {}
                    extra_var_dict[key] = extra_vars[key]
                    playbook_call += ' -e "%s" ' % extra_var_dict
                else:
                    playbook_call += " -e %s=\"'%s'\"" % (key, extra_vars[key])

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
                    playbook_call += " --%s %s" % (key.replace('_', '-'), run_options[key])

        if ans_verbosity:
            playbook_call += " -%s" % ans_verbosity

        logger.debug(playbook_call)
        output = exec_local_cmd_pipe(playbook_call, logger)
        return output


class Inventory(LoggerMixin):
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

        # set & create the inventory directory
        self.inv_dir = os.path.join(data_dir, 'inventory')
        if not os.path.isdir(self.inv_dir):
            os.makedirs(self.inv_dir)

        # set the master inventory
        self.master_inv = os.path.join(self.inv_dir, 'master')

        # set the unique inventory
        self.unique_inv = os.path.join(self.inv_dir, 'unique-%s' % uuid4())

        # defines the custom group to run the play against
        self.group = 'hosts'

    def create_master(self):
        """Create the master ansible inventory.

        This method will create a master inventory which contains all the
        hosts in the given scenario. Each host will have a group/group:vars.
        """
        # do not create master inventory if already exists
        if os.path.exists(self.master_inv):
            return

        # create parser object, raw config parser allows keys with no values
        config = RawConfigParser(allow_no_value=True)
        # disable default behavior to set values to lower case
        config.optionxform = str

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

            # add ip address to group
            if isinstance(host.ip_address, list):
                for item in host.ip_address:
                    config.set(section, item)
            elif isinstance(host.ip_address, str):
                config.set(section, host.ip_address)

            # add host vars
            for k, v in host.ansible_params.items():
                if k in ['ansible_ssh_private_key_file']:
                    v = os.path.join(getattr(host, 'workspace'), v)
                config.set(section_vars, k, v)

        # write the inventory
        with open(self.master_inv, 'w') as f:
            config.write(f)

        self.logger.debug("Master inventory content")
        self.log_inventory_content(config)

    def create_unique(self):
        """Create the unique ansible inventory.

        This method will create a unique inventory which contains placeholders
        for all hosts in the scenario. Along with a child group containing
        all the hosts for the action to run on.
        """
        # create parser object, raw config parser allows keys with no values
        config = RawConfigParser(allow_no_value=True)
        # disable default behavior to set values to lower case
        config.optionxform = str
        main_section = self.group + ":children"
        config.add_section(main_section)

        # add place holders for all hosts
        for host in self.all_hosts:
            config.add_section(host.name)

        # add specific hosts to the group to run the action against
        for host in self.hosts:
            config.set(main_section, host.name)

        # write the inventory
        with open(self.unique_inv, 'w') as f:
            config.write(f)

        self.logger.debug("Unique inventory content")
        self.log_inventory_content(config)

    def create(self):
        """Create the inventory."""
        self.create_master()
        self.create_unique()

    def delete_master(self):
        """Delete the master inventory file generated."""
        try:
            os.remove(self.master_inv)
        except OSError as ex:
            self.logger.warning(ex)

    def delete_unique(self):
        """Delete the unique inventory file generated."""
        try:
            os.remove(self.unique_inv)
        except OSError as ex:
            self.logger.warning(ex)
            self.logger.warning('You may experience problems with future '
                                'ansible calls due to additional inventory '
                                'files in the same inventory directory.')

    def delete(self):
        """Delete all ansible inventory files."""
        self.delete_unique()
        self.delete_master()

    def log_inventory_content(self, parser):
        # log the inventory file content
        for section in parser.sections():
            self.logger.debug('Section-> %s' % section)
            for item in parser.items(section):
                self.logger.debug(item)


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
        self._hosts = getattr(package, 'hosts')
        self.options = getattr(package, '%s_options' % self.name)
        self.galaxy_options = getattr(package, '%s_galaxy_options' % self.name)
        self.script = getattr(package, '%s_script' % self.name)
        self.config = getattr(package, 'config')
        self.all_hosts = getattr(package, 'all_hosts')
        self.workspace = self.config['WORKSPACE']
        self._action = os.path.join(self.workspace, getattr(package, 'name'))

        # create inventory object for create/delete inventory file
        self.inv = Inventory(
            self.hosts,
            self.all_hosts,
            data_dir=self.config['DATA_FOLDER']
        )

    def validate(self):
        """Validate that action is valid and exists."""
        found = os.path.exists(self.action)
        msg = 'Action %s ' % self.action
        if found:
            msg += 'found!'
            self.logger.debug(msg)
        else:
            msg += 'not found!'
            self.logger.error(msg)
            raise CarbonOrchestratorError(msg)

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

            cmd = 'ansible-galaxy install -r %s' % f
            results = exec_local_cmd_pipe(cmd, self.logger)

            if results[0] != 0:
                raise CarbonOrchestratorError(
                    'A problem occurred while installing roles using req. file'
                    ' %s' % f)
            self.logger.info('Roles installed successfully from: %s!' % f)

        if 'roles' in self.galaxy_options:
            if flag >= 1:
                self.logger.warning('FYI roles were already installed using a'
                                    ' requirements file. Problems may occur.')

            for item in self.galaxy_options['roles']:
                cmd = 'ansible-galaxy install %s' % item
                results = exec_local_cmd_pipe(cmd, self.logger)

                if results[0] != 0:
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

        # lets create the ansible inventory file to run the given action on
        # its associated hosts
        self.inv.create()

        # create an ansible controller object
        obj = AnsibleController(self.inv.inv_dir)

        # configure playbook variables
        extra_vars = dict(hosts=self.inv.group)

        ans_verbosity = get_ans_verbosity(self.logger, self.config)

        # download ansible roles (if applicable)
        self.download_roles()

        if self.script:
            # running a script, using the ansible script module

            run_options = {}

            # override ansible options (user passed vals for specific action)
            for val in self.user_run_vals:
                if self.options and val in self.options and self.options[val]:
                    run_options[val] = self.options[val]

            extra_args = None

            if self.options and 'extra_args' in self.options and \
                    self.options['extra_args']:
                extra_args = self.options['extra_args']

            if self._hosts:
                extra_vars["localhost"] = False
            else:
                extra_vars["localhost"] = True

            self.logger.debug("Extra variables used: " + str(extra_vars))
            self.logger.debug("Extra arguments used: " + str(extra_args))
            results = obj.run_module(
                "script",
                extra_vars=extra_vars,
                script=self.action,
                run_options=run_options,
                extra_args=extra_args,
                logger=self.logger,
                ans_verbosity=ans_verbosity
            )
        else:
            # If not a script then it must be a playbook

            if self.options and 'extra_vars' in self.options and \
                    self.options['extra_vars']:
                extra_vars.update(self.options['extra_vars'])

            self.logger.info('Executing action: %s.' % self.action)

            run_options = {}

            if "tags" in self.options and self.options["tags"]:
                run_options["tags"] = self.options["tags"]

            # override ansible options (user passed vals for specific action)
            for val in self.user_run_vals:
                if self.options and val in self.options and self.options[val]:
                    run_options[val] = self.options[val]

            self.logger.debug("Ansible options used: " + str(run_options))
            self.logger.debug("Extra variables being used: " + str(extra_vars))
            results = obj.run_playbook(
                self.action,
                extra_vars=extra_vars,
                run_options=run_options,
                ans_verbosity=ans_verbosity,
                logger=self.logger
            )

        self.logger.info('Finished action: %s execution.' % self.action)
        self.logger.info('Status => %s.' % results[0])

        # get ansible logs as needed
        self.alog_update()

        # delete the unique inventory particular to this run
        self.inv.delete_unique()

        # raise an exception if the ansible action failed
        if results[0] != 0:
            raise CarbonOrchestratorError(
                'Ansible action did not return a valid return code!'
            )
