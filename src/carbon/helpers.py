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

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import inspect
import json
import pkgutil
import random
import string
import sys
from logging import getLogger
from subprocess import Popen, PIPE

import os
import stat
import yaml

from flask.helpers import get_root_path

from .constants import PROVISIONERS

LOG = getLogger(__name__)

# sentinel
_missing = object()


class HelpersError(Exception):
    """Base class for carbon helpers exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(HelpersError, self).__init__(message)


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


def get_default_provisioner(provider):
    """
    Given a provider, it will return the default provisioner
    :param provider: the provider value
    :return: the default provisioner
    """
    provisioner_name = PROVISIONERS[provider.__provider_name__]
    return get_provisioner_class(provisioner_name)


def get_provisioners_list():
    """
    Returns a list of all the valid provisioners.
    :return: list of provisioners
    """
    valid_provisioners = []
    for provisioner_class in get_provisioners_classes():
        valid_provisioners.append(provisioner_class.__provisioner_name__)
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


def get_ansible_inventory_script(provider):
    """Return the absolute path to the ansible dynamic inventory script for
    the provider given.

    All inventory scripts are stored at ~ carbon.utils and use the following
    naming standard ~ provider_inventory.py.

    :param provider: Name of the provider.
    :return: Absolute path to script.
    """
    from . import utils

    _script = '%s_inventory.py' % provider
    inventory = os.path.join(get_root_path(utils.__name__), _script)

    # ensure the invetory file exists
    if not os.path.isfile(inventory):
        LOG.warn('Ansible inventory script not found for provider %s', provider)
        return None

    # ensure the inventory is marked executable for owners, group and others
    # exactly like -rwxrwxr-x.
    os.chmod(inventory,
             stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH |
             stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
             stat.S_IWUSR | stat.S_IWGRP)

    return inventory


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
    :rtype: object
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
                yaml.dump(content, f_raw, default_flow_style=False)
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


def check_is_gitrepo_fine(git_repo_url):
    """
    :param git_repo_url: a git url to validate
    :return: Boolean if the git url is good or not
    :rtype: Boolean
    """

    try:
        p = Popen(["git", "ls-remote", git_repo_url], stdout=PIPE)
        output = p.communicate()[0]
        if p.returncode != 0:
            LOG.warn('Unable to access %s - Returncode %s - Output %s',
                     git_repo_url, p.returncode, output)
            return False
    except:
        LOG.error(sys.exc_info()[0])
        LOG.error('Unable to access %s', git_repo_url)
        return False

    return True


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
