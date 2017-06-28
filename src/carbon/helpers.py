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
import sys
import stat
import os
import inspect
import json
import pkgutil
import random
import string
import threading

import yaml
import pexpect

from ._compat import string_types
from logging import getLogger
from subprocess import Popen, PIPE

from .constants import PROVISIONERS

LOG = getLogger(__name__)

# sentinel
_missing = object()


class HelpersException(Exception):
    """Base class for carbon helpers exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(HelpersException, self).__init__(message)


def get_root_path(import_name):
    """Returns the path to a package or cwd if that cannot be found.  This
    returns the path of a package or the folder that contains a module.

    :copyright: (c) 2015 by Armin Ronacher.
    """
    # Module already imported and has a file attribute.  Use that first.
    mod = sys.modules.get(import_name)
    if mod is not None and hasattr(mod, '__file__'):
        return os.path.dirname(os.path.abspath(mod.__file__))

    # Next attempt: check the loader.
    loader = pkgutil.get_loader(import_name)

    # Loader does not exist or we're referring to an unloaded main module
    # or a main module without path (interactive sessions), go with the
    # current working directory.
    if loader is None or import_name == '__main__':
        return os.getcwd()

    # Some other loaders might exhibit the same behavior.
    if hasattr(loader, 'get_filename'):
        filepath = loader.get_filename(import_name)
    else:
        # Fall back to imports.
        __import__(import_name)
        mod = sys.modules[import_name]
        filepath = getattr(mod, '__file__', None)

        # If we don't have a filepath it might be because we are a
        # namespace package.  In this case we pick the root path from the
        # first module that is contained in our package.
        if filepath is None:
            raise RuntimeError('No root path can be found for the provided '
                               'module "%s".  This can happen because the '
                               'module came from an import hook that does '
                               'not provide file name information or because '
                               'it\'s a namespace package.  In this case '
                               'the root path needs to be explicitly '
                               'provided.' % import_name)

    # filepath is import_name.py for a module, or __init__.py for a package.
    return os.path.dirname(os.path.abspath(filepath))


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
    :param name: the name of the provider
    :return: the provider class
    """
    return [provider.__provider_name__ for provider in get_providers_classes()]


def get_tasks_from_resource(resource):
    """
    Get the list of tasks from a resour
    :return:
    """
    tasks = []
    return tasks


def get_all_resources_from_scenario(scenario):
    """
    Given the scenario, it returns a list of all resources from
    the scenario, including the scenario itself.
    :param scenario: the scenario resource to get resources extracted from
    :return: list of resources
    """
    resources_list = []
    return resources_list


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
        raise HelpersException("Unknown file operation: %s." % operation)


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


def gen_key():
    """
    helper function to locally generate an ssh key
    """
    out = ""
    cmd = 'ssh-keygen'

    LOG.info('\tgen_key - Executing cmd: {}'.format(cmd))
    child = pexpect.spawn(cmd)

    while True:
        i = child.expect([pexpect.TIMEOUT,
                          r'Enter file in which to save the key',
                          r'Overwrite', r'Enter passphrase',
                          r'Enter same passphrase again:',
                          r'The key fingerprint is:',
                          pexpect.EOF], timeout=60)

        if i == 0:  # Timeout
            LOG.info('\t    Timeout...')
            LOG.info('\t    Failed to generate keys')
            LOG.info('\t{0}{1}'.format(child.before.replace('\n', '\n\t'),
                                       child.after.replace('\n', '\n\t')))
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.close()
            LOG.info("\n\tOutput Capture:\n\t" + "-" * 50)
            LOG.info("\t{}".format(out.replace('\n', '\n\t')))
            LOG.info("\t" + "-" * 50 + "\n")
            return 1

        if i == 1:  # File to save
            LOG.info('\t    Save File: Answer - Default')
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.sendline('')

        if i == 2:  # Overite
            LOG.info('\t    Save File exists: Answer - (yes/no)')
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.sendline('yes')

        if i == 3:  # passphrase
            LOG.info('\t    Passphrase: Answer - Default')
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.sendline('')

        if i == 4:  # confirm passphrase
            LOG.info('\t    Confirm Passphrase: Answer - Default')
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.sendline('')

        if i == 5:  # Finished.
            out = "{0}{1}{2}".format(out, child.before, child.after)

        if i == 6:  # Completed
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.close()

            LOG.info("\tOutput Capture\n" + "-" * 60 +
                     "\n\t{}\n".format(out.replace('\n', '\n\t')) +
                     "-" * 60 + "\n")

            if child.exitstatus == 0:
                LOG.info('    Succesfully generated keys')
                retcode = 0
            else:
                LOG.error('    Failed to generate keys')
                retcode = 1
            return retcode

    LOG.info('\tUnexpected Results...')
    LOG.error('Failed to generate keys')
    return 1


def copy_key(user, presponse, use_ips, test_system, sshkeypath):
    """
    helper funciton to inject ssh keys to a test system
    :param user: username of the test system
    :param presponse: password of the test system
    :param use_ips: Boolean to use ip or hostname
    :param test_system: dictionary of name and ip
    :param sshkeypath: full path of the public sshkey
    :return: return code
    :rtype: int
    """
    out = ""

    if use_ips == 'yes':
        cmd = 'ssh-copy-id -i {0} {1}@{2}'.format(sshkeypath, user, test_system['ip'])
    else:
        cmd = 'ssh-copy-id -i {0} {1}@{2}'.format(sshkeypath, user, test_system['name'])

    LOG.debug('Executing cmd: %s' % cmd)

    child = pexpect.spawn(cmd)

    while True:
        i = child.expect([pexpect.TIMEOUT, r'yes/no', r'password:',
                          r"added extra keys that you weren't expecting.",
                          pexpect.EOF], timeout=180)

        if i == 0:  # Timeout
            LOG.info('\t    Timeout...')
            LOG.info('\t    Failed to send keys to remote')
            LOG.info('\t{0}{1}'.format(child.before.replace('\n', '\n\t'),
                                       child.after.replace('\n', '\n\t')))
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.close()
            LOG.info("\n\tOutput Capture:\n" + "-" * 50)
            LOG.info("\t{}".format(out.replace('\n', '\n\t')))
            LOG.info("\t" + "-" * 50 + "\n")
            return 1

        if i == 1:  # yes no
            LOG.debug('\t    Answer: (yes/no)')
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.sendline('yes')

        if i == 2:  # Password
            LOG.debug('\t    Answer: Password')
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.sendline(presponse)

        if i == 3:  # finished.
            out = "{0}{1}{2}".format(out, child.before, child.after)

        if i == 4:  # Completed
            out = "{0}{1}{2}".format(out, child.before, child.after)
            child.close()
            if child.exitstatus == 0:
                LOG.info('\tSuccesfully sent keys to remote\n')
                retcode = 0
            else:
                LOG.error('Failed to send keys to remote\n')
                retcode = 1
            LOG.info("\n\tOutput Capture:\n\t" + "-" * 50 + "\n\t"
                     "{}".format(out.replace('\n', '\n\t')) + "\n\t" +
                     "-" * 50 + "\n")
            return retcode

    LOG.info('\tUnexpected Results...')
    LOG.error('Failed to send keys to remote\n')
    return 1


def send_key(user, presponse, use_ips, systems, sshkeypath):
    """
    setup for injecting ssh keys to test systems
    :param user: username of the test system
    :param presponse: password of the test system
    :param use_ips: Boolean to use ip or hostname
    :param test_system: dictionary of name and ip
    :param sshkeypath: full path of the public sshkey
    :return: return code
    :rtype: int
    """
    # Check if presponse is string or list
    host_pw_pairs = None
    # If string, construct key value pairs with same password for each host
    # for backward compatibility
    if isinstance(presponse, string_types):
        host_pw_pairs = [(system, presponse) for system in systems]
    # If list, zip the host and password lists together
    else:
        host_pw_pairs = zip(systems, presponse)
    # Send key to root and test users on test systems
    for test_system, host_presponse in host_pw_pairs:
        res = copy_key(user, host_presponse, use_ips, test_system, sshkeypath)
        if res:
            LOG.error("PRE: Failed to send keys to user {0} on system "
                      "{1}\n".format(user, test_system['name']))
            return 1
            raise Exception("Failed to send key. System: {0} - User: "
                            "{1}".format(test_system, user))
        else:
            LOG.info("PRE: Successfully sent keys to user {0} on system "
                     "{1}\n".format(user, test_system['name']))
    return 0


class LockedCachedProperty(object):
    """
    A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value.  Works like the one in Werkzeug but has a lock for
    thread safety.

    :copyright: (c) 2015 by Armin Ronacher.
    """

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func
        self.lock = threading.RLock()

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        with self.lock:
            value = obj.__dict__.get(self.__name__, _missing)
            if value is _missing:
                value = self.func(obj)
                obj.__dict__[self.__name__] = value
            return value


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
