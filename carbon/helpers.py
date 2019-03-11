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
    carbon.helpers

    Module containing classes and functions which are generic and used
    throughout the code base.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import inspect
import json
import logging
import os
import pkgutil
import random
import re
import socket
import string
import subprocess
import sys
import time
import warnings
from logging import getLogger

import cachetclient.cachet as cachet
import jinja2
import requests
import urllib3
import yaml
from paramiko import SSHClient, WarningPolicy
from paramiko.ssh_exception import SSHException, BadHostKeyException, \
    AuthenticationException

from ._compat import string_types, is_py2
from .constants import PROVISIONERS, RULE_HOST_NAMING
from .exceptions import CarbonError, HelpersError

LOG = getLogger(__name__)

# sentinel
_missing = object()


def get_core_tasks_classes():
    """
    Go through all modules within carbon.tasks package and return
    the list of all tasks classes within it. All tasks within the carbon.tasks
    module are considered valid task class to be added into the pipeline.
    :return: List of all valid tasks classes
    """
    from .core import CarbonTask
    from . import tasks

    # all task classes must
    prefix = tasks.__name__ + "."

    tasks_list = []

    # Run through each module within tasks and take the list of
    # classes that are subclass of CarbonTask but not CarbonTask itself.
    # When you import a class within a module, it becames a member of
    # that class
    for importer, modname, ispkg in pkgutil.iter_modules(tasks.__path__, prefix):
        if str(modname).endswith('.ext'):
            continue
        clsmembers = inspect.getmembers(sys.modules[modname], inspect.isclass)
        for clsname, clsmember in clsmembers:
            if (clsmember is not CarbonTask) and issubclass(clsmember, CarbonTask):
                tasks_list.append(clsmember)

    return tasks_list


def get_provisioners_classes():
    """Go through all modules within carbon.provisioners package and return
    the list of all provisioners classes within it. All provisioners within
    the carbon.provisioners package are considered valid provisioners classes
    to be used by Carbon framework.
    :return: List of all provisioners classes"""
    from .core import CarbonProvisioner
    from . import provisioners

    # all task classes must
    prefix = provisioners.__name__ + "."

    provisioners_list = []

    # Run through each module within tasks and take the list of
    # classes that are subclass of CarbonTask but not CarbonTask itself.
    # When you import a class within a module, it becames a member of
    # that class
    for importer, modname, ispkg in pkgutil.iter_modules(provisioners.__path__, prefix):
        if str(modname).endswith('.ext'):
            continue
        clsmembers = inspect.getmembers(sys.modules[modname], inspect.isclass)
        for clsname, clsmember in clsmembers:
            if (clsmember is not CarbonProvisioner) and issubclass(clsmember, CarbonProvisioner):
                provisioners_list.append(clsmember)

    return provisioners_list


def get_provisioners_plugin_classes():
    """Go through all modules within carbon.provisioners package and return
    the list of all provisioner gateway classes within it. All provisioners within
    the carbon.provisioners.ext package are considered valid provisioner gateway classes
    to be used by Carbon framework.
    :return: List of all provisioner gateway classes"""

    from .core import ProvisionerPlugin
    from . import provisioners

    # all task classes must
    prefix = provisioners.__name__ + "."

    provisioners_list = []

    # Run through each module within tasks and take the list of
    # classes that are subclass of CarbonTask but not CarbonTask itself.
    # When you import a class within a module, it becames a member of
    # that class
    for importer, modname, ispkg in pkgutil.walk_packages(provisioners.__path__, prefix):
        if str(modname).endswith('.ext') or str(modname).endswith('.blueprint'):
            continue
        clsmembers = inspect.getmembers(sys.modules[modname], inspect.isclass)
        for clsname, clsmember in clsmembers:
            if (clsmember is not ProvisionerPlugin) and issubclass(clsmember, ProvisionerPlugin):
                provisioners_list.append(clsmember)

    return provisioners_list


def get_default_provisioner(provider=None):
    """
    Given a provider, it will return the default provisioner
    :param provider: the provider value
    :return: the default provisioner
    """

    if provider is None:
        provisioner_name = PROVISIONERS['host']
    else:
        provisioner_name = PROVISIONERS[provider.__provider_name__]
    return get_provisioner_class(provisioner_name)


def get_default_provisioner_plugin(provider=None):
    if provider is not None:
        for plugin_class in get_provisioners_plugin_classes():
            if plugin_class.__plugin_name__.startswith(provider.__provider_name__):
                return plugin_class
    else:
        return get_provisioner_plugin_class('linchpin')


def get_provisioners_list():
    """
    Returns a list of all the valid provisioners.
    :return: list of provisioners
    """
    valid_provisioners = []
    for provisioner_class in get_provisioners_classes():
        valid_provisioners.append(provisioner_class.__provisioner_name__)
    return valid_provisioners


def get_provisioners_plugins_list():
    """
    Returns a list of all the valid provisioner gateways.
    :return: list of provisioner gateways
    """
    valid_provisioners = []
    for provisioner_gateway_class in get_provisioners_plugin_classes():
        valid_provisioners.append(provisioner_gateway_class.__plugin_name__)
    return valid_provisioners


def get_provisioner_class(name):
    """Return the provisioner class based on the __provisioner_name__ set
    within the class. See ~carbon.core.CarbonProvisioner for more information.
    :param name: The name of the provisioner
    :return: The provisioner class
    """
    for provisioner in get_provisioners_classes():
        if provisioner.__provisioner_name__ == name:
            return provisioner


def get_provisioner_plugin_class(name):
    """Return the provisioner gateway class based on the __provisioner_name__ set
    within the class. See ~carbon.core.CarbonPlugin for more information.
    :param name: The name of the provisioner
    :return: The provisioner gateway class
    """
    for provisioner in get_provisioners_plugin_classes():
        if provisioner.__plugin_name__.startswith(name):
            return provisioner


def get_providers_classes():
    """
    Go through all modules within carbon.providers package and return
    the list of all providers classes within it. All providers within the
    carbon.providers package are considered valid providers classes to be
    used by Carbon framework.
    :return: List of all providers classes
    """
    from .core import CarbonProvider
    from . import providers

    # all task classes must
    prefix = providers.__name__ + "."

    providers_list = []

    # Run through each module within tasks and take the list of
    # classes that are subclass of CarbonTask but not CarbonTask itself.
    # When you import a class within a module, it becames a member of
    # that class
    for importer, modname, ispkg in pkgutil.iter_modules(providers.__path__, prefix):
        if str(modname).endswith('.ext'):
            continue
        clsmembers = inspect.getmembers(sys.modules[modname], inspect.isclass)
        for clsname, clsmember in clsmembers:
            if (clsmember is not CarbonProvider) and issubclass(clsmember, CarbonProvider):
                providers_list.append(clsmember)

    return providers_list


def get_provider_class(name):
    """
    Return the provider class based on the __provider_name__ set within
    the class. See ~carbon.core.CarbonProvider for more information.
    :param name: the name of the provider
    :return: the provider class
    """
    for provider in get_providers_classes():
        if provider.__provider_name__ == name:
            return provider


def get_providers_list():
    """
    Return the provider class based on the __provider_name__ set within
    the class.
    :return: the provider class
    """
    return [provider.__provider_name__ for provider in get_providers_classes()]


def get_orchestrators_classes():
    """Go through all available orchestrator modules and return all the
    classes.

    :return: orchestrator classes
    :rtype: list
    """
    from .core import CarbonOrchestrator
    from . import orchestrators

    prefix = orchestrators.__name__ + '.'

    orchestrators_list = []

    for importer, modname, ispkg in pkgutil.iter_modules(orchestrators.__path__, prefix):
        if str(modname).endswith('.ext'):
            continue
        clsmembers = inspect.getmembers(sys.modules[modname], inspect.isclass)
        for clsname, clsmember in clsmembers:
            if (clsmember is not CarbonOrchestrator) and issubclass(clsmember, CarbonOrchestrator):
                orchestrators_list.append(clsmember)
    return orchestrators_list


def get_orchestrator_class(name):
    """Return the orchestrator class based on the __orchestrator_name__ set
    within the class. See ~carbon.core.CarbonOrchestrator for more information.

    :param name: the name of the orchestrator
    :return: the orchestrator class
    """
    for orchestrator in get_orchestrators_classes():
        if orchestrator.__orchestrator_name__ == name:
            return orchestrator


def get_orchestrators_list():
    """Return a list of available orchestrators.

    :return: orchestrators
    """
    return [orchestrator.__orchestrator_name__ for orchestrator in
            get_orchestrators_classes()]


def get_executors_classes():
    """Go through all available executor modules and return all the
    classes.

    :return: executor classes
    :rtype: list
    """
    from .core import CarbonExecutor
    from . import executors

    prefix = executors.__name__ + '.'

    executors_list = []

    for importer, modname, ispkg in pkgutil.iter_modules(executors.__path__, prefix):
        if str(modname).endswith('.ext'):
            continue
        clsmembers = inspect.getmembers(sys.modules[modname], inspect.isclass)
        for clsname, clsmember in clsmembers:
            if (clsmember is not CarbonExecutor) and issubclass(clsmember, CarbonExecutor):
                executors_list.append(clsmember)
    return executors_list


def get_executor_class(name):
    """Return the executor class based on the __executor_name__ set
    within the class. See ~carbon.core.CarbonExecutor for more information.

    :param name: the name of the executor
    :return: the executor class
    """
    for executor in get_executors_classes():
        if executor.__executor_name__ == name:
            return executor


def get_executors_list():
    """Return a list of available executors.

    :return: executors
    """
    return [executor.__executor_name__ for executor in
            get_executors_classes()]


def gen_random_str(char_num=8):
    """
    Generate a string with a specific number of characters, defined
    by `char_num`.

    :param char_num: the number of characters for the random string
    :return: random string
    """
    return ''.join(random.SystemRandom().
                   choice(string.ascii_lowercase + string.digits) for
                   _ in range(char_num))


def file_mgmt(operation, file_path, content=None, cfg_parser=None):
    """A generic function to manage files (read/write).

    :param operation: File operation type to perform
    :type operation: str
    :param file_path: File name including path
    :type file_path: str
    :param content: Data to write to a file
    :type content: object
    :param cfg_parser: Config parser object (Only needed if the file being
        processed is a configuration file parser language)
    :type cfg_parser: bool
    :return: Data that was read from a file
    """

    # Determine file extension
    file_ext = os.path.splitext(file_path)[-1]

    if operation in ['r', 'read']:
        # Read
        if os.path.exists(file_path):
            if file_ext == ".json":
                # json
                with open(file_path) as f_raw:
                    return json.load(f_raw)
            elif file_ext in ['.yaml', '.yml']:
                # yaml
                with open(file_path) as f_raw:
                    return yaml.load(f_raw)
            else:
                # text
                with open(file_path) as f_raw:
                    if cfg_parser is not None:
                        # Config parser file
                        return cfg_parser.readfp(f_raw)
                    else:
                        return f_raw.read()
        else:
            raise IOError("%s file not found!" % file_path)
    elif operation in ['w', 'write']:
        # Write
        mode = 'w+' if os.path.exists(file_path) else 'w'
        if file_ext == ".json":
            # json
            with open(file_path, mode) as f_raw:
                json.dump(content, f_raw, indent=4, sort_keys=True)
        elif file_ext in ['.yaml', '.yml']:
            # yaml
            with open(file_path, mode) as f_raw:
                yaml.safe_dump(content, f_raw, default_flow_style=False)
        else:
            # text
            with open(file_path, mode) as f_raw:
                if cfg_parser is not None:
                    # Config parser file
                    cfg_parser.write(f_raw)
                else:
                    f_raw.write(content)
    else:
        raise HelpersError("Unknown file operation: %s." % operation)


def is_url_valid(url):
    """Check if a url is valid.

    :param url: URL path.
    :type url: str
    :return: True if url exists or false if url does not exist.
    :rtype: bool
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.HTTPError as ex:
        LOG.error(ex)
        return False
    return True


def template_render(filepath, env_dict):
    """
    A function to do jinja templating given a file and a dictionary of key/vars

    :param filepath: path to a file
    :param env_dict: dictionary of key/values used for data substitution
    :return: stream of data with the templating complete
    :rtype: data stream
    """
    path, filename = os.path.split(filepath)
    return jinja2.Environment(loader=jinja2.FileSystemLoader(
        path)).get_template(filename).render(env_dict)


def exec_local_cmd(cmd):
    """Execute command locally."""
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    rc = proc.wait()
    output = ""
    err = ""
    for l in proc.stdout.readlines():
        output += l.decode('utf-8').strip()
    for l in proc.stderr.readlines():
        err += l.decode('utf-8').strip()
    # LOG.debug(output)
    return rc, output, err
    # output = proc.communicate()
    # return proc.returncode, output[0], output[1]


def exec_local_cmd_pipe(cmd, logger):
    """Execute command locally, and pipe output in real time.

    :param cmd: command to run
    :type cmd: str
    :param logger: logger object
    :type logger: object
    :return: tuple of rc and error (if there was an error)
    """
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=2,
        close_fds=True
    )
    while True:
        output, error = ("", "")
        if proc.poll is not None:
            output = proc.stdout.readline().decode('utf-8')
        if output == "" and error == "" and proc.poll() is not None:
            break
        if output:
            logger.info(output.strip())
    rc = proc.poll()
    if rc != 0:
        error = proc.stderr.readline().decode('utf-8')
    return rc, error


class CustomDict(dict):
    """Carbon dictionary to represent a resource from JSON or YAML.

    Initialized a data (loaded JSON or YAML) and creates a
    dict object with attributes to be accessed via dot notation
    or as a dict key-value.

    Deeper parameters within the data that contain its own data
    are also represented as Resource
    """

    def __init__(self, data={}):
        super(CustomDict, self).__init__(data)
        for key, value in data.items():
            if isinstance(value, dict):
                value = CustomDict(value)
            self[key] = value

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)


def fetch_hosts(hosts, task, all_hosts=True):
    """Set the hosts for a task requiring hosts.

    This method is helpful for action/execute resources. These resources
    need the actual host objects instead of the referenced string name for
    the host in the given scenario descriptor file.

    It will fetch the correct hosts if the hosts for the given task are
    either string or host class type.

    :param hosts: scenario hosts
    :type hosts: list
    :param task: task requiring hosts
    :type task: dict
    :param all_hosts: determine to set all hosts
    :type all_hosts: bool
    :return: updated task object including host objects
    :rtype: dict
    """

    # placeholders
    _hosts = list()
    _all_hosts = list()
    _filtered_hosts = list()
    _type = None

    # determine the task attribute where hosts are stored
    if 'resource' in task:
        _type = 'resource'
    elif 'package' in task:
        _type = 'package'

    # determine the task host data types
    if all(isinstance(item, string_types) for item in task[_type].hosts):
        for host in hosts:
            if all_hosts:
                _all_hosts.append(host)
            if 'all' in task[_type].hosts:
                _hosts.append(host)
                continue
            if host.name in task[_type].hosts:
                _hosts.append(host)
            for r in host.role:
                if r in task[_type].hosts:
                    _hosts.append(host)
    else:
        for host in hosts:
            if all_hosts:
                _all_hosts.append(host)
            for task_host in task[_type].hosts:
                if host.name == task_host.name:
                    _hosts.append(host)
                    break

    task[_type].hosts = _hosts
    task[_type].all_hosts = _all_hosts
    return task


def filter_host_name(name):
    """
    A host name is limited to max 20 characters and ruled
    by the RULE_HOST_NAMING regex pattern defined in
    constants.

    :param name: the name to be filtered
    :return: 20 characters filtered name
    """
    result = RULE_HOST_NAMING.sub('', name)
    return str(result[:20]).lower()


def ssh_retry(obj):
    """
    Decorator to check SSH Connection before method execution.
    Will perform 30 retries with sleep of 10 seconds
    between attempts
    """
    MAX_ATTEMPTS = 30
    MAX_WAIT_TIME = 10

    def check_access(*args, **kwargs):
        """
        SSH Connection check and retries
        """
        # Set flag and Inventory
        ssh_errs = False
        args[0].set_inventory()

        host_group = kwargs['extra_vars']['hosts']
        inv_groups = args[0].inventory.groups
        if host_group not in inv_groups:
            raise HelpersError(
                'ERROR: Unexpected error - Group %s not found in inventory file!' % kwargs['extra_vars']['hosts']
            )

        for group in inv_groups[host_group].child_groups:
            sys_vars = group.vars
            server_ip = group.hosts[0].address

            # skip ssh connectivity check if server is localhost
            if is_host_localhost(server_ip):
                continue

            server_user = sys_vars['ansible_user']
            server_key_file = sys_vars['ansible_ssh_private_key_file']

            # Perform SSH checks
            attempt = 1
            while attempt <= MAX_ATTEMPTS:
                try:
                    ssh = SSHClient()
                    ssh.set_missing_host_key_policy(WarningPolicy())

                    # Test ssh connection
                    ssh.connect(server_ip,
                                username=server_user,
                                key_filename=server_key_file,
                                timeout=5)
                    LOG.debug("Server %s - IP: %s is reachable." %
                              (group, server_ip))
                    ssh.close()
                    break
                except (BadHostKeyException, AuthenticationException,
                        SSHException, socket.error) as ex:
                    attempt = attempt + 1
                    LOG.error(ex.strerror)
                    LOG.error("Server %s - IP: %s is unreachable." % (group,
                                                                      server_ip))
                    if attempt <= MAX_ATTEMPTS:
                        LOG.info('Attempt %s of %s: retrying in %s seconds' %
                                 (attempt, MAX_ATTEMPTS, MAX_WAIT_TIME))
                        time.sleep(MAX_WAIT_TIME)

            # Check Max SSH Retries performed
            if attempt > MAX_ATTEMPTS:
                LOG.error(
                    'Max Retries exceeded. SSH ERROR - Resource unreachable - Server %s - IP: %s!' %
                    (group, server_ip)
                )
                ssh_errs = True

        # Check for SSH Errors
        if ssh_errs:
            raise HelpersError(
                'ERROR: Unable to establish ssh connection with resources!'
            )

        # Run Playbook/Module
        result = obj(*args, **kwargs)
        return result

    return check_access


def resource_check(scenario, config):
    """
    External Component Dependency Check
    Throws exception if all components are not UP

    :param scenario: carbon scenario object
    :param config: carbon config object
    """

    # External Dependency Check
    # Available components to check ci-rhos, zabbix-sysops, brew, covscan
    #                             polarion, rpmdiff, umb, errata, rdo-cloud
    #                             gerrit
    if config['RESOURCE_CHECK_ENDPOINT']:
        endpoint = config['RESOURCE_CHECK_ENDPOINT']
        ext_resources_avail = True
        component_names = scenario.resource_check
        urllib3.disable_warnings()
        components = cachet.Components(endpoint=endpoint, verify=False)
        LOG.info(' DEPENDENCY CHECK '.center(64, '-'))
        for comp in component_names:
            comp_resource_invalid = False
            comp_resource_avail = False
            for attempts in range(1, 6):
                component_data = components.get(params={'name': comp})
                if json.loads(component_data)['data']:
                    comp_status = json.loads(component_data)['data'][0]['status']
                    if comp_status == 4:
                        comp_resource_avail = False
                        time.sleep(30)
                        continue
                    else:
                        comp_resource_avail = True
                        break
                else:
                    comp_resource_invalid = True
            if comp_resource_avail is not True or comp_resource_invalid is True:
                ext_resources_avail = False
            if comp_resource_invalid:
                LOG.info('{:>40} {:<9} - Attempts {}'.format(
                    comp.upper(), ': INVALID', attempts))
            else:
                LOG.info('{:>40} {:<9} - Attempts {}'.format(
                    comp.upper(), ': UP' if comp_resource_avail else ': DOWN', attempts))
        warnings.resetwarnings()
        LOG.info(''.center(64, '-'))

        if ext_resources_avail is not True:
            LOG.error("ERROR: Not all external resources are available or valid. Not running scenario")
            raise CarbonError(
                'Scenario %s will not be run! Not all external resources are available or valid' %
                scenario.name
            )


def get_ans_verbosity(logger, config):
    ans_verbosity = None

    if "ANSIBLE_VERBOSITY" in config and \
            config["ANSIBLE_VERBOSITY"]:
        ans_verbosity = config["ANSIBLE_VERBOSITY"]
    else:
        ans_verbosity = 'v'

    return ans_verbosity


class DataInjector(object):
    """Data injector class.

    This class is primarily used for injecting data into strings which the
    data to be replaced needs to come from a host resource. It is helpful
    in the cases where orchestrate or execute tasks require additional data.
    i.e. ip address, metadata, authentication details, etc.

    ---

    How does this work?

    You have a command in your definition file that needs the ip address of a
    host resource.

    command: /usr/bin/foo --ip { host01.ip_address[0] } --args ..

    The host01 is a resource defined in the provision section of carbon and
    the ip_address is an attribute of the host01. This class will evaluate
    the string and lookup the ip_address[0] from the host01 resource object
    and update the string with the correct information. This makes it helpful
    when orchestrate/execute tasks require data from the hosts itself.
    """
    def __init__(self, hosts):
        """Constructor.

        :param hosts: carbon host resources
        :type hosts: list
        """
        self.hosts = hosts

        # regular expression to search for in the string
        # data to be injected needs to be in the format of
        # { host01.metadata.k1 }
        self.regexp = r"\{(.*?)\}"

    def host_exist(self, node):
        """Determine if the host defined in the string formatted var is valid.

        In the case no host is found, an exception is raised.

        :param node: node name
        :type node: str
        :return: carbon host resource matching based on node input
        :rtype: object
        """
        for host in self.hosts:
            if node == getattr(host, 'name'):
                return host
        raise CarbonError('Node %s not found!' % node)

    def inject(self, command):
        """Main worker.

        This method will perform the data injection.

        :param command: command to inject data into
        :type command: str
        :return: updated command
        :rtype: str
        """
        variables = list(map(str.strip, re.findall(self.regexp, command)))

        if not variables.__len__():
            return command

        for variable in variables:
            value = None
            _vars = variable.split('.')
            node = _vars.pop(0)

            # verify variable has a valid host set
            host = self.host_exist(node)

            for index, item in enumerate(_vars):
                try:
                    # is the item intended to be a position in a list, if so
                    # get the key and position
                    key = item.split('[')[0]
                    pos = int(item.split('[')[1].split(']')[0])

                    if value:
                        # get the latest value from the dictionary
                        value = value[key][pos]
                    else:
                        # get latest value from host
                        if hasattr(host, key) and index <= 0:
                            value = getattr(host, key)[pos]
                            if isinstance(value, str):
                                break

                    # is the value a dict, if so keep going!
                    if isinstance(value, dict):
                        continue
                except IndexError:
                    # item is not intended to be a position in a list

                    # check if the item is an attribute of the host
                    if hasattr(host, item) and index <= 0:
                        value = getattr(host, item)

                        if isinstance(value, str):
                            # we know the value has no further traversing to do
                            break
                        # value is either a list or dict, more traversing to do
                        continue
                    else:
                        if value is None:
                            raise AttributeError('%s not found in host %s!' %
                                                 (item, getattr(host, 'name')))

                    # check if the item's value is a dict and update the value
                    # for further traversing to do
                    try:
                        if isinstance(value[item], dict):
                            value = value[item]
                            continue
                    except KeyError:
                        raise CarbonError('%s not found in %s' % (item, value))

                    # final check to get value no more traversing required
                    if value:
                        value = value[item]
                except KeyError:
                    raise CarbonError('Unable to locate item %s!' % item)

            command = command.replace('{ %s }' % variable, value)
        return command


def is_host_localhost(host_ip):
    """Determine if the host ip address given is localhost.

    Since it can be hard to determine if the host is localhost, we will
    initially verify its localhost if the ip_address has a value of either:
        - 127.0.0.1
        - localhost
    If the host ip_address is either of those, then we know that the machine
    is the localhost.

    :param host_ip: host resource ip address
    :type host_ip: str
    :return: whether the ip address is localhost or not
    :rtype: bool
    """
    if host_ip not in ['127.0.0.1', 'localhost']:
        return False
    return True
