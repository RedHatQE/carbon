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
import fnmatch
import stat
import cachetclient.cachet as cachet
import jinja2
import requests
import urllib3
from paramiko import RSAKey
from ruamel.yaml.comments import CommentedMap as OrderedDict
from collections import OrderedDict
from ruamel.yaml import YAML
import yaml
from paramiko import SSHClient, WarningPolicy
from paramiko.ssh_exception import SSHException, BadHostKeyException, \
    AuthenticationException
from ._compat import string_types
from .constants import PROVISIONERS, RULE_HOST_NAMING, IMPORTER, DEFAULT_TASK_CONCURRENCY, \
    TASKLIST
from .exceptions import CarbonError, HelpersError
import pkg_resources

LOG = getLogger(__name__)

# sentinel
_missing = object()


def get_actions_failed_status(action_list):
    """
    Go through the action_list and return actions with failed status.
    If no action with failed status is found the original list is returned
    :return: List of actions based on its status
    """
    for index, action_item in enumerate(action_list):
        if action_item.status == 1:
            new_list = action_list[index:]
            return new_list
    return action_list


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


'''
# TODO Need to refactor asset provisioner and remove/refactor these classes
# TODO get_provisioners_classes, get_provisioner_class, get_default_provisioner
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


def get_provisioner_class(name):
    """Return the provisioner class based on the __provisioner_name__ set
    within the class. See ~carbon.core.CarbonProvisioner for more information.
    :param name: The name of the provisioner
    :return: The provisioner class
    """
    for provisioner in get_provisioners_classes():
        if provisioner.__provisioner_name__ == name:
            return provisioner


def get_default_provisioner(provider=None):
    """
    Given a provider, it will return the default provisioner
    :param provider: the provider value
    :return: the default provisioner
    """

    if provider is None:
        provisioner_name = PROVISIONERS['asset']
    else:
        try:
            provisioner_names = PROVISIONERS[provider.__provider_name__]
            if isinstance(provisioner_names, list):
                provisioner_name = provisioner_names[0]
        except KeyError:
            provisioner_name = 'linchpin-wrapper'

    return get_provisioner_class(provisioner_name) '''


# Using entry point to get the provisioners defined in carbon's setup.py file
def get_provisioners_plugin_classes():
    """Return all provisioner plugin classes discovered by carbon
    :return: The list of provisioner plugin classes
    """
    provisioner_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('provisioner_plugins'):
        provisioner_plugin_dict[entry_point.name] = entry_point.load()
    return provisioner_plugin_dict


def get_default_provisioner_plugin(provider=None):
    """Return provisioner plugin classe based on the given provider class. If provider is None linchpin_wrapper plugin
    class is returned as the default provisioner class
    :param provider: The provider class
    :return: The provisioner plugin class
    """
    if provider is not None:
        provisioners = PROVISIONERS[provider.__provider_name__]
        if isinstance(provisioners, list):
            return get_provisioner_plugin_class(provisioners[0])
        else:
            return get_provisioner_plugin_class(provisioners)
    else:
        return get_provisioner_plugin_class('linchpin_wrapper')


def get_provisioners_plugins_list():
    """
    Returns a list of all the valid provisioner gateways.
    :return: list of provisioner gateways
    """

    valid_provisioners = []
    for provisioner_gateway_class in get_provisioners_plugin_classes().values():
        valid_provisioners.append(provisioner_gateway_class.__plugin_name__)
    return valid_provisioners


def get_provisioner_plugin_class(name):
    """Return the provisioner gateway class based on the __provisioner_name__ set
    within the class. See ~carbon.core.CarbonPlugin for more information.
    :param name: The name of the provisioner
    :return: The provisioner gateway class
    """
    for provisioner in get_provisioners_plugin_classes().values():
        if provisioner.__plugin_name__.startswith(name):
            return provisioner


# Using entry point to get the providers from within carbon as well as the ones coming from the external plugins
def get_provider_plugin_classes():
    """Return all provider plugin classes discovered by carbon
    :return: The list of provider plugin classes
    """
    provider_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('provider_plugins'):
        provider_plugin_dict[entry_point.name] = entry_point.load()
    return provider_plugin_dict


def get_provider_plugin_class(name):
    """
    Return the provider class based on the __provider_name__ set within
    the class.
    :param name: the name of the provider
    :return: the provider class
    """
    for provider in get_provider_plugin_classes().values():
        if provider.__provider_name__ == name:
            return provider


def get_provider_plugin_list():
    """
    Return the list of provider class based on the __provider_name__ set within
    the class.
    :return: list of the the provider names
    """
    return [provider.__provider_name__ for provider in get_provider_plugin_classes().values()]


# Using entry point to get the orchestrators defined in carbon's setup.py file
def get_orchestrators_plugin_classes():
    """Return all orchestrator plugin classes discovered by carbon
    :return: The list of orchestrator plugin classes
    """
    orchestrator_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('orchestrator_plugins'):
        orchestrator_plugin_dict[entry_point.name] = entry_point.load()
    return orchestrator_plugin_dict.values()


def get_orchestrator_plugin_class(name):
    """Return the orchestrator class based on the __orchestrator_name__ set
    within the class.

    :param name: the name of the orchestrator
    :return: the orchestrator class
    """
    for orchestrator in get_orchestrators_plugin_classes():
        if orchestrator.__orchestrator_name__ == name:
            return orchestrator


def get_orchestrators_plugin_list():
    """Return a list of available orchestrators.

    :return: orchestrators
    """
    return [orchestrator.__orchestrator_name__ for orchestrator in
            get_orchestrators_plugin_classes()]


# Using entry point to get the executors defined in carbon's setup.py file
def get_executors_plugin_classes():

    """Return all executor plugin classes discovered by carbon
    :return: The list of executor plugin classes
    """
    executor_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('executor_plugins'):
        executor_plugin_dict[entry_point.name] = entry_point.load()
    return executor_plugin_dict.values()


def get_executor_plugin_class(name):
    """Return the executor class based on the __executor_name__ set
    within the class.

    :param name: the name of the executor
    :return: the executor class
    """
    for executor in get_executors_plugin_classes():
        if executor.__executor_name__ == name:
            return executor


def get_executors_plugin_list():
    """Return a list of available executors.

    :return: executors
    """
    return [executor.__executor_name__ for executor in
            get_executors_plugin_classes()]


# Using entry point to get the importers. These methods are being used to get the importer plugins external to carbon
def get_importers_plugin_classes():
    """Return all importer plugin classes discovered by carbon
    :return: The list of importer plugin classes
    """
    ext_plugin_dict = {}
    for entry_point in pkg_resources.iter_entry_points('importer_plugins'):
        ext_plugin_dict[entry_point.name] = entry_point.load()
    return ext_plugin_dict.values()


def get_default_importer_plugin_class(provider):
    """Return the importer class based on the provider name
    :param provider: The provider class
    :return: The importer plugin class
    """
    for plugin_class in get_importers_plugin_classes():
        if plugin_class.__plugin_name__.startswith(provider.__provider_name__):
            return plugin_class


def get_importers_plugin_list():
    """
    Returns a list of all the valid importer gateways.
    :return: list of importer plugin names
    """
    valid_reporters = []
    for reporter_plugin_class in get_importers_plugin_classes():
        valid_reporters.append(reporter_plugin_class.__plugin_name__)
    return valid_reporters


def get_importer_plugin_class(name):
    """Return the importer plugin class based on the __plugin_name__ set
    within the class.
    :param name: The name of the importer
    :return: The importer plugin class
    """
    for reporter in get_importers_plugin_classes():
        if reporter.__plugin_name__.startswith(name):
            return reporter


def is_provider_mapped_to_provisioner(provider, provisioner):
    """
    Given a provider and a provisioner, check if they are supported together.
    :param provider:
    :param provisioner:
    :return:
    """

    for provider_key, prov_val in PROVISIONERS.items():
        if getattr(provider, '__provider_name__') == provider_key:
            if isinstance(prov_val, list):
                for p in prov_val:
                    if p == provisioner:
                        return True
            else:
                if prov_val == provisioner:
                    return True
    return False


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
    # to maintain the sequence in the results.yml file with ruamel
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.Representer.add_representer(OrderedDict, yaml.Representer.represent_dict)

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
                yaml.dump(content, f_raw)
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
    output = proc.communicate()
    return proc.returncode, output[0].decode('utf-8'), output[1].decode('utf-8')


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


def fetch_assets(hosts, task, all_hosts=True):
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
            if host.name in task[_type].hosts or [h for h in task[_type].hosts if h in host.name]:
                _hosts.append(host)
                continue
            if hasattr(host, 'role'):
                for r in host.role:
                    if r in task[_type].hosts:
                        _hosts.append(host)
            elif hasattr(host, 'groups'):
                for g in host.groups:
                    if g in task[_type].hosts:
                        _hosts.append(host)
    else:
        for host in hosts:
            if all_hosts:
                _all_hosts.append(host)
            for task_host in task[_type].hosts:
                # additional check task_host.name in host.name was put in case when linchpin count was
                # used and there are host resources with names matching original resource name
                if host.name == task_host.name or task_host.name in host.name:
                    _hosts.append(host)
                    break

    task[_type].hosts = _hosts
    task[_type].all_hosts = _all_hosts
    return task


def fetch_executes(executes, hosts, task):
    """Set the executes for a task requiring executes.

    This method is helpful for report resources. These resources
    need the actual execute objects instead of the referenced string name for
    the execute in the given scenario descriptor file.

    It will fetch the correct execute if the execute for the given task are
    either string or execute class type.

    :param executes: scenario executes
    :type executes: list
    :param hosts: scenario hosts
    :type hosts: list
    :param task: task requiring executes
    :type task: dict
    :return: updated task object including execute objects
    :rtype: dict
    """

    # placeholders
    _executes = list()
    _type = None

    # determine the task attribute where hosts are stored
    if 'resource' in task:
        _type = 'resource'
    elif 'package' in task:
        _type = 'package'

    # determine the task host data types
    if all(isinstance(item, string_types) for item in task[_type].executes):
        for e in executes:
            if e.name in task[_type].executes:
                # fetch hosts to be used later for data injection
                dummy_task = dict()
                dummy_task[_type] = e
                dummy_task = fetch_assets(hosts, dummy_task)
                _executes.append(dummy_task[_type])
    else:
        for e in executes:
            for task_execute in task[_type].executes:
                if e.name == task_execute.name:
                    # fetch hosts to be used later for data injection
                    dummy_task = dict()
                    dummy_task[_type] = e
                    dummy_task = fetch_assets(hosts, dummy_task)
                    _executes.append(dummy_task[_type])
                    break

    if not _executes:
        # Kept having issues tyring to import the Execute
        # resource to make a dummy Execute with all the hosts
        # so this is a hack way of assigning the hosts.
        task[_type].all_hosts = hosts
    else:
        task[_type].executes = _executes
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
                    LOG.error(ex)
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

        # regex to check jsonpath strings
        self.exclusion_chk_str = r"^range|^[|.|$|@]|[\w|']+:"

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
            if re.match(self.exclusion_chk_str, variable):
                LOG.debug("JSONPath format was identified in the command %s." % variable)
                continue
            else:
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

    def inject_dictionary(self, dictionary):
        """
        inject data into a dictionary where
        data-passthrough template is encountered

        :param dictionary:
        :return:
        """
        injected_dict = dict()

        for key, value in dictionary.items():
            inj_key = self.inject(key)
            if isinstance(value, list):
                inj_val = [self.inject(v) for v in value]
            elif isinstance(value, dict):
                inj_val = self.inject_dictionary(value)
            elif isinstance(value, string_types):
                inj_val = self.inject(value)
            else:
                inj_val = value
            injected_dict.update({inj_key: inj_val})

        return injected_dict


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


'''
def find_artifacts_on_disk(data_folder, path_list, art_location_found=True):
    """
    Use by the Artifact Importer to search a list of paths in the data folder
    to see if they exist. If the Execute collected artifacts, it will check the
    current runs unique data_folder/artifacts and the .results/artifacts/ specifically
    for the artifacts.

    If the Execute did not collect artifacts, it will walk the data_folder and the .results
    looking for the artifacts

    :param data_folder: the unique data_folder id
    :type data_folder: path as a string
    :param path_list: The list of artifacts to look for
    :type path_list: a list containing a string of paths
    :param art_location_found: Whether the Executes object collected artifacts
    :type art_location_found: Boolean
    :return: a list of artifacts that were found to be imported.
    """

    # iterate the list of paths to confirm they exist locally
    total_paths = len(path_list)
    fnd_paths = list()

    if art_location_found:

        # Check the path in data_folder first and then in .results folder

        result_dir = os.path.join(os.path.dirname(data_folder), '.results')
        for p in path_list:
            if check_path_exists(p, data_folder):
                fnd_paths.append(os.path.abspath(os.path.join(data_folder, p)))
            elif check_path_exists(p, result_dir):
                fnd_paths.append(os.path.abspath(os.path.join(result_dir, p)))

    else:
        walked_list = walk_results_directory(data_folder)
        for p in path_list:
            regquery = build_artifact_regex_query(p)
            matches = [regquery.search(p) for p in walked_list]
            fnd_paths = [m.string for m in matches if m]

    if fnd_paths:
        for f in fnd_paths:
            LOG.info('Artifact %s has been found!' % os.path.basename(f))
            LOG.debug('Full path to artifact on disk: %s' % f)

    if not fnd_paths:
        LOG.error('Did not find any of the artifacts on local disk. '
                    'Import cannot occur!')

    if total_paths < len(fnd_paths):
        LOG.warning('Found %s artifacts. Will still attempt to import the'
                    ' artifacts that were found' % len(fnd_paths))
    else:
        LOG.warning('Found %s out of %s artifacts. Will still attempt to import the'
                    ' artifacts that were found' % (len(fnd_paths), total_paths))
    return fnd_paths
    '''


def find_artifacts_on_disk(data_folder, report_name, art_location=[]):
    """
    Use by the Artifact Importer to search a list of paths in the data folder
    to see if they exist. If the Execute collected artifacts, it will check the
    current runs unique data_folder/artifacts and the .results/artifacts/ specifically
    for the artifacts.

    If the Execute did not collect artifacts, it will walk the data_folder and the .results
    looking for the artifacts

    :param data_folder: the unique data_folder id
    :type data_folder: path as a string
    :param path_list: The list of artifacts to look for
    :type path_list: a list containing a string of paths
    :param art_location_found: Whether the Executes object collected artifacts
    :type art_location_found: Boolean
    :return: a list of artifacts that were found to be imported.
    """

    # iterate the list of paths to confirm they exist locally
    # total_paths = len(path_list)
    fnd_paths = list()
    path_list = list()

    regquery = build_artifact_regex_query(report_name)
    path_list.extend(search_artifact_location_dict(art_location, report_name, regquery))

    # Check the path in data_folder first and then in .results folder
    result_dir = os.path.join(os.path.dirname(data_folder), '.results')
    for p in path_list:
        if check_path_exists(p, data_folder):
            fnd_paths.append(os.path.abspath(os.path.join(data_folder, p)))
        elif check_path_exists(p, result_dir):
            fnd_paths.append(os.path.abspath(os.path.join(result_dir, p)))

    walked_list = walk_results_directory(data_folder, fnd_paths)
    matches = [regquery.search(p) for p in walked_list]
    fnd_paths.extend([m.string for m in matches if m])

    if fnd_paths:
        for f in fnd_paths:
            LOG.info('Artifact %s has been found!' % os.path.basename(f))
            LOG.debug('Full path to artifact on disk: %s' % f)

    if not fnd_paths:
        LOG.error('Did not find any of the artifacts on local disk. '
                  'Import cannot occur!')

    return fnd_paths


def check_path_exists(element, dir):
    # check if the path exists
    return os.path.exists(os.path.abspath(os.path.join(dir, element)))


def search_artifact_location_dict(art_locations, report_name, reg_query):
    """
    Use by the Artifact Importer to search a list of collected
    artifacts by the Execute phase using regex to search for the report name

    :param art_locations: the list of files collected during Execute
    :type art_locations: list of string paths
    :param report_name: The artifact to look for
    :type report_name: a string of an artifact name, can contain regex
    :param reg_query: The regex query to use to search the artifact_location
    :type reg_query: regexquery object
    :return: a list containing the artifacts found
    """
    artifacts_path = []

    if art_locations:
        full_path = [os.path.join(dir, f) for dir, file_list in art_locations.items() for f in file_list]
        for f in full_path:
            LOG.debug('These are the artifact_locations in the execute: %s' % f)
        matches = [reg_query.search(p) for p in full_path]
        artifacts_path = [m.string for m in matches if m]

        for fn in artifacts_path:
            LOG.debug('Found the following artifact, %s, that matched %s in artifact_location' % (fn, report_name))

    return artifacts_path


def walk_results_directory(dir, path_list):
    """
    Used to walk the data directory and .results directory
    when the artifact in question is not in the list of
    artifacts collected by Execute

    :param dir: The data_folder dir
    :type dir: string dir path
    :param path_list: The list of pathes that was found in artifact_locations
    :type path_list: List
    :return: a list containing all the paths from data_folder and .results
    """

    data_dir_list = []

    # Carbon specific folders in datafolder and .results folder
    exclude = ['logs', 'rp_logs', 'rp_payload', 'inventory']

    # iterate over the data folder first
    for root, dirs, files in os.walk(dir):
        # Excluding carbon specific folders
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in files:
            p = os.path.abspath(os.path.join(root, f))
            if p not in path_list:
                LOG.debug(p)
                data_dir_list.append(p)

    # iterate over the results folder next
    result_dir = os.path.join(os.path.dirname(dir), '.results')
    for root, dirs, files in os.walk(result_dir):
        # Excluding carbon specific folders
        dirs[:] = [d for d in dirs if d not in exclude]
        for f in files:
            p = os.path.abspath(os.path.join(root, f))
            if p not in path_list:
                data_dir_list.append(p)

    return data_dir_list


def build_artifact_regex_query(name):
    """
    Used to build a regex query from the artifact
    name which could contain file matching pattern.

    :param name: The artifact name
    :type name: string
    :return: a compiled regex query
    """

    regex = fnmatch.translate(name)
    regquery = re.compile(regex)
    return regquery


def validate_render_scenario(scenario):
    """
    This method takes the absolute path of the scenario descriptor file and returns back a list of
    data streams of scenario(s) after doing the following checks:
    (1) Checks there is no yaml.safe_load error for the provided scenario file
    (2) Checks for include section present in the scenario file
    (3) Checks the include section has valid scenario file path and it is not empty
    (4) Checks there is no yaml.safe_load error for scenario file in the include section
    :param scenario: scenario file path
    :type scenario: str
    :return: scenario data stream(s)
    :rtype: list of data streams
    """
    scenario_stream_list = list()
    try:
        data = yaml.safe_load(template_render(scenario, os.environ))
        # adding master scenario as the first scenario data stream
        scenario_stream_list.append(template_render(scenario, os.environ))
        if 'include' in data.keys():
            include_item = data['include']
            include_template = list()
            if include_item is not None:
                for item in include_item:
                    if os.path.isfile(item):
                        item = os.path.abspath(item)
                        # check to verify the data in included scenario is valid
                        try:
                            yaml.safe_load(template_render(item, os.environ))
                            include_template.append(template_render(item, os.environ))
                        except yaml.YAMLError:
                            # raising Carbon error to differentiate the yaml issue is with included scenario
                            raise CarbonError('Error loading updated included scenario data!')
                    else:
                        # raising HelperError if included file is invalid or included section is empty
                        raise HelpersError('Included File is invalid or Include section is empty .'
                                           'You have to provide valid scenario files to be included.')
                scenario_stream_list.extend(include_template)
    except yaml.YAMLError as e:
        # here raising yaml error to differentiate yaml issue is with main scenario
        raise e
    return scenario_stream_list


def ssh_key_file_generator(workspace, ssh_key_param):
    """
    A method to find if the ssh key value in a provider
    param is a path to a public or private key. If it
    is a public key, just return the key back. If it
    is a private key, generate the public key from it
    and return that back.

    Right now this is only really used by Linchpin
    in the LinchpinResourceBuilder class for Beaker
    resources because they expect a public key and the
    various ssh key options in their resource defintions

    :param workspace: the Carbon workspace keys directory
    :type workspace: path as a string
    :param ssh_key_param: the ssh_key from the provider param
    :type ssh_key_param: value of the ssh_key param either a path or an actual key
    :return: a path to a public key
    """

    # setup absolute path for key
    key = os.path.join(workspace, ssh_key_param)

    # set permission of the key
    try:
        os.chmod(key, stat.S_IRUSR | stat.S_IWUSR)
    except OSError as ex:
        raise HelpersError(
            'Error setting private key file permissions: %s' % ex
        )

    # Lets assume it's a private key file and try to load it
    # and create a public key for it
    try:
        rsa_key = RSAKey.from_private_key_file(key)
        # generate public key from private
        public_key = os.path.join(
            workspace, ssh_key_param + ".pub"
        )
        with open(public_key, 'w') as f:
            f.write('%s %s\n' % (rsa_key.get_name(), rsa_key.get_base64()))
        return public_key
    except SSHException:
        # Exception means the key file was invalid.
        # Assume it's a public key and return it
        return key


def lookup_ip_of_hostname(host_name):
    """
    A method to find the ip of the hostname.
    This is used by Linchpin specifically for Beaker
    since 99% of the systems in beaker are by FQDN host name.
    To make sure the IP address field in the carbon Asset resource
    is an actual IP address we need to look it up


    :param host_name: the FQDN of the host
    :type host_name: string
    :return: return a string containing the ip
    """
    return socket.gethostbyname(host_name)


def set_task_class_concurrency(task, resource):
    """
    set the task __concurrency__ field in the class
    to whatever was passed in the config
    :param task:
    :type task: CarbonTask class
    :param resource:
    :type CarbonResource object
    :return: CarbonTask class
    """
    val = getattr(resource, 'config')['TASK_CONCURRENCY'].get(task['task'].__task_name__.upper())
    if val == 'True':
        val = True
    else:
        val = False
    task['task'].__concurrent__ = val
    return task


def mask_credentials_password(credentials):
    """
    Mask the credentials that could get printed out
    to stdout or carbon_output.log

    :param credentials:
    :return: credentials dict
    """
    asteriks = ''
    masked_creds = dict()
    for k, v in credentials.items():
        for p in ['password', 'token', 'key']:
            if p not in k:
                continue
            else:
                for i in range(0, len(v)):
                    asteriks += '*'
        if asteriks != '':
            masked_creds.update({k: asteriks})
            asteriks = ''
            continue
        masked_creds.update({k: v})

    return masked_creds


def sort_tasklist(user_tasks):
    """
    :param user_tasks:
    :return: Array of tasks
    """

    return sorted(user_tasks, key=TASKLIST.index)


class LinchpinResourceBuilder(object):

    """
    LinchpinResourceBuilder Class used by the Linchpin
    provisioner plugin to be able to take the dictionary
    parameters in a Carbon Provider and build a proper
    Linchpin resource definition dictionary that can be used
    to build the resource group

    """

    _bkr_op_list = ['like', '==', '!=', '<=', '>=', '=', '<', '>']

    @classmethod
    def build_linchpin_resource_definition(cls, provider, host_params):
        """
        main public method for Linchpin provisioner to interact with.

        :param provider: the Carbon Provider to validate against
        :type Object: Provider object
        :param host_params: the Asset Resource profile dictionary
        :type dict: dictionary
        :return: a Linchpin resource definition dictionary
        """
        provider_name = getattr(provider, '__provider_name__')
        if provider_name == 'beaker':
            return cls._build_beaker_resource_definition(provider, host_params)
        elif provider_name == 'openstack':
            return cls._build_openstack_resource_definition(provider, host_params)
        elif provider_name == 'libvirt':
            return cls._build_libvirt_resource_defintion(provider, host_params)
        elif provider_name == 'aws':
            return cls._build_aws_resource_defintion(provider, host_params)

    @classmethod
    def _build_beaker_resource_definition(cls, provider, host_params):
        """
        Private beaker specific method to build the resource definition. It
        will call the sub methods to build the recipe set, the root
        resource definition, and combine them.

        :param provider: the Carbon Provider to validate against
        :type Object: Provider object
        :param host_params: the Asset Resource profile dictionary
        :type dict: dictionary
        :return: a Linchpin resource definition dictionary
        """

        # Check that the provider params
        cls._check_key_exist_in_provider(provider, host_params)

        # Build the recipe set
        rs = cls._build_beaker_recipe_set(provider, host_params)

        # Build the resource def
        rd = cls._build_beaker_resource(host_params)

        # Update the recipe set and resource def with proper ssh params
        # if ssh param is a key_file
        if rs.get('ssh_key_file', None):
            key_dir = os.path.dirname(rs.get('ssh_key_file')[0])
            files = [os.path.basename(f) for f in rs.get('ssh_key_file')]
            if os.path.dirname(key_dir) == '.':
                key_dir = os.path.abspath(key_dir)
            rd['ssh_keys_path'] = key_dir
            rs['ssh_key_file'] = files

        # Add the recipe set to resource def
        rd.update(dict(recipesets=[rs]))

        return rd

    @classmethod
    def _build_beaker_resource(cls, host_params):
        """
        Private beaker specific method to build the root resource definition.

        :param host_params: the Asset Resource profile dictionary
        :return: a Linchpin resource definition dictionary
        """

        resource_def = dict(role='bkr_server')
        params = host_params['provider']

        # Add the resource def params
        for k, v in params.items():
            if k in ['whiteboard', 'max_attempts', 'attempt_wait_time',
                     'cancel_message', 'job_group']:
                resource_def[k] = v
            if k == 'jobgroup':
                resource_def['job_group'] = v

        return resource_def

    @classmethod
    def _build_beaker_recipe_set(cls, provider, host_params):
        """
        Private beaker specific method to build the beaker
        recipeset.

        :param provider: the Carbon Provider to validate against
        :type Object: Provider object
        :param host_params: the Asset Resource profile dictionary
        :type dict: dictionary
        :return: a Linchpin resource definition dictionary
        """

        recipe_set = dict(count=1)
        params = host_params['provider']

        # Build the recipe set with required parameters
        for k, v in params.items():
            for item in provider.req_params:
                if k == item[0]:
                    recipe_set[k] = v

        # Next add the common parameters
        for k, v in params.items():
            if k == 'whiteboard':
                continue
            for item in provider.comm_opt_params:
                if k == item[0] and k == 'kickstart':
                    recipe_set[k] = os.path.abspath(os.path.join(host_params['workspace'], v))
                    continue
                if k == item[0]:
                    recipe_set[k] = v

        # Next add the linchpin common params that differ in name or type
        for k, v in params.items():
            if k == 'ssh_key':
                continue
            if k == 'job_group':
                continue
            for lp, lt in provider.linchpin_comm_opt_params:
                if k == lp:
                    recipe_set[k] = v

        # Next add the carbon common params that differ in name or type
        # but do the conversion to linchpin name or type.
        for k, v in params.items():
            for cp, ct in provider.carbon_comm_opt_params:
                if k == cp and k == 'tag':
                    for lp, lt in provider.linchpin_comm_opt_params:
                        if lp == 'tags':
                            if not isinstance(v, lt[0]):
                                recipe_set[lp] = [v]
                            else:
                                recipe_set[lp] = v
                if k == cp and k == 'kernel_options':
                    for lp, lt in provider.linchpin_comm_opt_params:
                        if lp == 'kernel_options':
                            if not isinstance(v, lt[0]):
                                ko = ""
                                for i in v:
                                    ko += "%s " % i
                                recipe_set[lp] = ko.strip()
                            else:
                                recipe_set[lp] = v
                if k == cp and k == 'kernel_post_options':
                    for lp, lt in provider.linchpin_comm_opt_params:
                        if lp == 'kernel_options_post':
                            if not isinstance(v, lt[0]):
                                kop = ""
                                for i in v:
                                    kop += "%s " % i
                                recipe_set[lp] = kop.strip()
                            else:
                                recipe_set[lp] = v
                if k == cp and k == 'host_requires_options':
                    for lp, lt in provider.linchpin_comm_opt_params:
                        if lp == 'hostrequires':
                            if dict not in v:
                                hr = []
                                for op in cls._bkr_op_list:
                                    for h in v:
                                        if op in h.strip():
                                            hrt, hrv = h.strip().split(op)
                                            if hrt.strip() in ['force', 'rawxml']:
                                                hr.append({hrt.strip(): hrv.strip()})
                                            else:
                                                hr.append(dict(tag=hrt.strip(),
                                                               op=op,
                                                               value=hrv.strip()))
                                recipe_set[lp] = hr
                            else:
                                recipe_set[lp] = v
                if k == cp and k == 'ksmeta':
                    for lp, lt in provider.linchpin_comm_opt_params:
                        if lp == 'ks_meta':
                            if not isinstance(v, lt[0]):
                                ksm = ""
                                for i in v:
                                    ksm += "%s " % i
                                recipe_set[lp] = ksm.strip()
                            else:
                                recipe_set[lp] = v
                if k == cp and k == 'key_values':
                    for lp, lt in provider.linchpin_comm_opt_params:
                        if lp == 'keyvalues':
                            recipe_set[lp] = v

                if k == cp and k == 'ssh_key':
                    if not isinstance(v, str):
                        keys = [key for key in v if 'ssh-rsa' in key]
                        if len(keys) > 0:
                            recipe_set[k] = keys
                        key_files = [ssh_key_file_generator(host_params['workspace'], kf) for kf in v
                                     if 'ssh-rsa' not in kf]
                        if len(key_files) > 0:
                            recipe_set['ssh_key_file'] = key_files
                    else:
                        recipe_set['ssh_key_file'] = [ssh_key_file_generator(host_params['workspace'], v)]

        # Add only the linchpin specific optional parameters
        for k, v in params.items():
            for item in provider.linchpin_only_opt_params:
                if item[0] == 'max_attempts':
                    continue
                if item[0] == 'attempt_wait_time':
                    continue
                if item[0] == 'cancel_message':
                    continue
                if item[0] == 'tx_id':
                    continue
                if k == item[0]:
                    recipe_set[k] = v

        # Add the node_id
        if params.get('node_id', None):
            if recipe_set.get('ids', None):
                recipe_set['ids'].append(params.get('node_id'))
            else:
                recipe_set['ids'] = [params.get('node_id')]

        # Finally, update the name with the real name
        recipe_set['name'] = host_params['name']

        return recipe_set

    @classmethod
    def _build_openstack_resource_definition(cls, provider, host_params):
        """
        Private openstack specific method to build the resource definition.

        :param provider: the Carbon Provider to validate against
        :type Object: Provider object
        :param host_params: the Asset Resource profile dictionary
        :type dict: dictionary
        :return: a Linchpin resource definition dictionary
        """

        resource_def = dict(role='os_server', count=1, verify='false')

        params = host_params['provider']
        creds = getattr(provider, 'credentials')

        # Check that the provider params
        cls._check_key_exist_in_provider(provider, host_params)

        # Add any of the op cred params:
        for key, value in creds.items():
            for cp, ct in provider.opt_credential_params:
                if key == cp and key == 'region':
                    resource_def['region_name'] = value

        # Add in all the required params
        for key, value in params.items():
            for cp, ct in provider.req_params:
                if key == cp:
                    resource_def[key] = value

        # Next add in all the common params
        for key, value in params.items():
            for cp, ct in provider.comm_opt_params:
                if key == cp:
                    resource_def[key] = value

        # Next add the common params that differ by    `
        # name or by type
        for key, value in params.items():
            for cp, ct in provider.linchpin_comm_opt_params:
                if key == cp:
                    resource_def[key] = value

        # Next add the linchpin only opt params
        for key, value in params.items():
            if key == 'tx_id':
                continue
            for cp, ct in provider.linchpin_only_opt_params:
                if key == cp:
                    resource_def[key] = value

        # Finally, add the carbon specific common
        # params that differ by name or type
        for key, value in params.items():
            for cp, ct in provider.carbon_comm_opt_params:
                if key == cp and not resource_def.get('fip_pool'):
                    resource_def['fip_pool'] = value

        # Update name with real name of host resource
        resource_def['name'] = host_params['name']

        return resource_def

    @classmethod
    def _build_libvirt_resource_defintion(cls, provider, host_params):

        resource_def = dict()
        params = host_params['provider']
        roles = getattr(provider, '_supported_roles')

        for p in provider.req_params:
            if p[0] in params:
                if params[p[0]] and params[p[0]] in roles:
                    for k, v in params.items():
                        if k in ['credential', 'hostname', 'tx_id', 'node_id']:
                            continue
                        resource_def[k] = v
                else:
                    LOG.error('The specified role type is not one of the supported types.')
                    raise HelpersError('One of the following roles must be specified %s.' % roles)

            else:
                LOG.error('Could not find the role key in the provider parameters.')
                raise HelpersError('The key, role, must be specified to build the resource definition properly.')

        # Update with the real host name
        resource_def['name'] = host_params['name']

        # Update with host specific keys
        if resource_def['role'].find('node') != -1:

            # remove the libvirt_evars if any were specified since they don't belong in the
            # topology file. Those get set as evars in the linchpin cfg.
            for evar in ['libvirt_image_path', 'libvirt_user', 'libvirt_become']:
                resource_def.pop(evar, None)

            # for xml key linchpin expects it in the linchpin workspace
            # need to copy it over to the workspace carbon setups in .results
            if resource_def.get('xml', None):
                xml_path = os.path.join(host_params.get('workspace'), resource_def.get('xml', None))
                lp_ws = os.path.join(
                    os.path.join(os.path.dirname(host_params.get('data_folder')), '.results'), 'linchpin')
                if not os.path.exists(xml_path):
                    raise HelpersError('The xml file does not appear to exist in the carbon workspace.')
                os.system('cp -r -f %s %s ' % (xml_path, lp_ws))
                resource_def.update(dict(xml=os.path.basename(xml_path)))

            # update count for a host resource
            if not resource_def.get('count', False):
                resource_def.update(dict(count=1))

        return resource_def

    @classmethod
    def _build_aws_resource_defintion(cls, provider, host_params):

        resource_def = dict()
        params = host_params['provider']
        roles = getattr(provider, '_supported_roles')

        for p in provider.req_params:
            if p[0] in params:
                if params[p[0]] and params[p[0]] in roles:
                    for k, v in params.items():
                        if k in ['credential', 'hostname', 'tx_id', 'node_id']:
                            continue
                        resource_def[k] = v
                else:
                    LOG.error('The specified role type is not one of the supported types.')
                    raise HelpersError('One of the following roles must be specified %s.' % roles)

            else:
                LOG.error('Could not find the role key in the provider parameters.')
                raise HelpersError('The key, role, must be specified to build the resource definition properly.')

        # Update with the real host name
        resource_def['name'] = host_params['name']

        # Update with host specific keys
        if resource_def['role'].find('ec2') != -1 and len(resource_def['role']) == 7:
            # update count for a host resource
            if not resource_def.get('count', False):
                resource_def.update(dict(count=1))

        # Update the specific params that deal with relative file path to be
        # abs pathes in the scenario workspace
        for key in resource_def:
            if key in ['policy_file', 'template_path']:
                if not os.path.isabs(key):
                    ws_abs = os.path.join(host_params.get('workspace'), key)
                    resource_def[key] = ws_abs

        return resource_def

    @classmethod
    def _check_key_exist_in_provider(cls, provider, host_params):

        provider_params = host_params['provider']

        provider_keys = [k[0] for k in provider.req_params]
        provider_keys.extend([k[0] for k in provider.comm_opt_params])
        provider_keys.extend([k[0] for k in provider.linchpin_comm_opt_params])
        provider_keys.extend([k[0] for k in provider.carbon_comm_opt_params])
        provider_keys.extend([k[0] for k in provider.linchpin_only_opt_params])

        # Openstack provider does not have carbon only options
        try:
            provider_keys.extend([k[0] for k in provider.carbon_only_opt_params])
        except AttributeError:
            pass

        for key in provider_params:
            if key in ['hostname', 'credential', 'node_id', 'job_url']:
                continue
            if key not in provider_keys:
                LOG.warning('specified key: %s is not one supported by the carbon provider. '
                            'It will be ignored. Please run carbon validate -s <scenario.yml> '
                            'to make sure you have the proper parameters.' % key)
