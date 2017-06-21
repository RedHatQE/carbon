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
    carbon.core

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import shutil
import sys
import os
import errno
import inspect
from distutils.dir_util import copy_tree

from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging import Formatter, getLogger, StreamHandler, FileHandler
from taskrunner import Task

from .helpers import get_core_tasks_classes


class CarbonException(Exception):
    """Carbon's base Exception class"""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        self.message = message
        super(CarbonException, self).__init__(message)


class CarbonTaskException(CarbonException):
    """Carbon's task base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonTaskException, self).__init__(message)


class CarbonResourceException(CarbonException):
    """Carbon's resource base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonResourceException, self).__init__(message)


class CarbonProvisionerException(CarbonException):
    """Carbon's provisioner base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonProvisionerException, self).__init__(message)


class CarbonProviderException(CarbonException):
    """Carbon's provider base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonProviderException, self).__init__(message)


class CarbonControllerException(CarbonException):
    """Carbon's controller base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonControllerException, self).__init__(message)


class LoggerMixinException(CarbonException):
    """Carbon's logger mixin base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonTaskException, self).__init__(message)


class LoggerMixin(object):
    """Carbons logger mixin class.

    This class provides an easy interface for other classes throughout carbon
    to utilize the carbon logger.

    When a carbon object is created, the carbon logger will be created also.
    Allowing easy access to the logger as follows:

        cbn = Carbon()
        cbn.logger.info('Carbon!')

    Carbon packages (classes) can either include the logger mixin or create
    their own object.

        class Host(CarbonResource):
            self.logger.info('Carbon Resource!')

    Modules that want to use carbon logger per function base and not per class,
    can access the carbon logger as follows:

        from logging import getLogger
        LOG = getLogger(__name__)
        LOG.info('Carbon!')

    New loggers for other libraries can easily be added. A create_lib_logger
    method will need to be create to setup the logger. Then lastly you can set
    a property to return that specific logger for easy access.
    """

    _LOG_FORMAT = ("%(asctime)s %(levelname)s "
                   "[%(name)s.%(funcName)s:%(lineno)d] %(message)s")

    _LOG_LEVELS = {
        'debug': DEBUG,
        'info': INFO,
        'warning': WARNING,
        'error': ERROR,
        'critical': CRITICAL
    }

    @classmethod
    def create_carbon_logger(cls, carbon_config):
        """Create carbons logger.

        :param name: Logger name.
        :param log_level: Log level to set for logger.
        :return: Carbon logger object.
        """
        clogger = getLogger(carbon_config["LOGGER_NAME"])
        if not clogger.handlers:
            if carbon_config["LOGGER_TYPE"] == "stream":
                chandler = StreamHandler()
            elif carbon_config["LOGGER_TYPE"] == "file":
                logfile = os.path.join(carbon_config["DATA_FOLDER"], "logs", "carbon_scenario.log")
                logdir = os.path.dirname(logfile)
                if os.path.exists(logdir):
                    pass
                else:
                    try:
                        os.makedirs(logdir)
                    except OSError as ex:
                        if ex.errno == errno.EACCES:
                            raise LoggerMixinException(
                                'You do not have permission to create the '
                                'workspace.'
                            )
                        else:
                            raise LoggerMixinException(
                                'Error creating scenario workspace: %s' %
                                ex.message
                            )
                chandler = FileHandler(logfile)
            else:
                raise LoggerMixinException(
                    'Please set a valid LOGGER_TYPE value.'
                )
            chandler.setLevel(cls._LOG_LEVELS[carbon_config["LOG_LEVEL"]])
            chandler.setFormatter(Formatter(cls._LOG_FORMAT))
            clogger.setLevel(cls._LOG_LEVELS[carbon_config["LOG_LEVEL"]])
            clogger.addHandler(chandler)
        return clogger

    @classmethod
    def create_custom_logger(cls, carbon_config, name):
        """Create custom logger.

        :param name: Logger name.
        :param log_level: Log level to set for logger.
        :param name: name of a python class to log
        :return: Taskrunner logger object.
        """
        if carbon_config["LOGGER_TYPE"] == "stream":
            thandler = StreamHandler()
        elif carbon_config["LOGGER_TYPE"] == "file":
            logfile = os.path.join(carbon_config["DATA_FOLDER"], "logs", "carbon_scenario.log")
            logdir = os.path.dirname(logfile)
            if os.path.exists(logdir):
                pass
            else:
                try:
                    os.makedirs(logdir)
                except OSError as ex:
                    if ex.errno == errno.EACCES:
                        raise LoggerMixinException(
                            'You do not have permission to create the '
                            'workspace.'
                        )
                    else:
                        raise LoggerMixinException(
                            'Error creating scenario workspace: %s' %
                            ex.message
                        )
            thandler = FileHandler(logfile)
        else:
            raise LoggerMixinException(
                'Please set a valid LOGGER_TYPE value.'
            )
        thandler.setLevel(cls._LOG_LEVELS[carbon_config["LOG_LEVEL"]])
        thandler.setFormatter(Formatter(cls._LOG_FORMAT))
        tlogger = getLogger(name)
        tlogger.setLevel(cls._LOG_LEVELS[carbon_config["LOG_LEVEL"]])
        tlogger.addHandler(thandler)
        return tlogger

    @property
    def logger(self):
        """Returns the default logger (carbon logger) object."""
        return getLogger(inspect.getmodule(inspect.stack()[1][0]).__name__)


class CarbonTask(Task, LoggerMixin):
    """
    This is the base class for every task created for Carbon framework.
    All instances of this class can be found within the ~carbon.tasks
    package.

    This class is an instance of taskrunner.Task.
    """

    def __init__(self, name=None, **kwargs):
        super(CarbonTask, self).__init__(**kwargs)

        if name is not None:
            self.name = name

    def run(self, context):
        pass

    def cleanup(self, context):
        pass

    def __str__(self):
        return self.name


class CarbonResource(LoggerMixin):
    """
    This is the base class for every resource created for Carbon Framework.
    All instances of this class can be found within ~carbon.resources
    package.
    """
    _valid_tasks_types = []
    _fields = []

    def __init__(self, config=None, name=None, **kwargs):

        # every resource has a name
        self._name = name

        # A list of tasks that will be executed upon the reource.
        self._tasks = []

        # Carbon configuration
        self._config = config

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError('You can set name after class is instanciated.')

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        raise AttributeError('You can set config after resource is created.')

    def _add_task(self, t):
        """
        Add a task to the list of tasks for the resource
        """
        if t['task'] not in set(get_core_tasks_classes()):
            raise CarbonResourceException(
                'The task class "%s" used is not valid.' % t['task']
            )
        self._tasks.append(t)

    def _extract_tasks_from_resource(self):
        """
        It checks every member of this class and compare if this is
        an instance of CarbonTask.

        # TODO: better if we return a generator
        :return: list of tasks for this class
        """
        lst = []
        for name, obj in inspect.getmembers(self, inspect.isclass):
            if issubclass(obj, CarbonTask):
                lst.append(name)
        return lst

    def load(self, data):
        """
        Given a dictionary of attributes, this function loads these
        attributes for this class.

        :param data: a dictionary with attributes for the resource
        """
        for key, value in data.items():
            # name has precedence when coming from a YAML file
            # if name is set through name=, it will be overwritten
            # by the YAML file properties.
            if key == 'name':
                self._name = value
            elif key in self._fields:
                setattr(self, key, value)
        if data:
            self.reload_tasks()

    def _get_task_constructors(self):
        return [getattr(self, "_construct_%s_task" % task_type)
                for task_type in self._valid_tasks_types]

    def get_asset_list(self):
        assets = []
        for host in self.hosts:
            # check for possible assets, and add filename if set
            for asset in host._assets:
                if asset:
                    # verify host has the key
                    if hasattr(host, asset):
                        # verify key value is set
                        if getattr(host, asset):
                            assets.append(getattr(host, asset))
                    # check creds
                    else:
                        for cred in self._credentials:
                            if asset in cred and cred[asset]:
                                assets.append(cred[asset])
        return assets

    def copy_assets(self):
        assets_dir = self.config["ASSETS_PATH"]
        data_folder = self.config["DATA_FOLDER"]
        for asset in self.get_asset_list():
            asset_src = os.path.join(assets_dir, asset)
            self.logger.debug("Attempt copy {0} {1}".format(asset_src, data_folder))
            try:
                shutil.copy(asset_src, data_folder)
            except IOError as e:
                # case where the source is a directory of files
                if e.errno == errno.EISDIR:
                    try:
                        copy_tree(asset_src, data_folder)
                    except:
                        e = sys.exc_info()[0]
                        raise CarbonException("Unexpected error, copying assets "
                                              "dir: {}".format(e))
                else:
                    raise CarbonException("Unexpected error, copying assets: "
                                          "{}".format(e))
            except:
                e = sys.exc_info()[0]
                raise CarbonException("unexpected error: {}".format(e))

    def reload_tasks(self):
        self._tasks = []
        for task_constructor in self._get_task_constructors():
            self._add_task(task_constructor())

    def dump(self):
        pass

    def get_tasks(self):
        return self._tasks

    def profile(self):
        raise NotImplementedError

    def validate(self):
        pass


class CarbonProvisioner(LoggerMixin):
    """
    This is the base class for all provisioners for provisioning machines
    """
    __provisioner_name__ = None

    def create(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    @property
    def name(self):
        return self.__provisioner__name__

    @name.setter
    def name(self, value):
        raise CarbonProvisionerException(
            'You can not set provisioner name property. This value is set by '
            'the instance.'
        )


class CarbonProvider(LoggerMixin):
    """
    This is the base class for all providers.

    Every host needs to be associated with a CarbonProvider. The
    subclasses of CarbonProvider needs to implement the validation
    functions for each mandatory and optional parameters. The format
    for the validation function signature is:

    @classmethod
    def validate_<parameter_name>(cls, value)


    """
    # the YAML definition uses this value to reference to this class.
    # you have to override this variable in the subclasses so it can be
    # referenced within the YAML definition with provider=...
    __provider_name__ = None
    __provider_prefix__ = None

    _mandatory_parameters = ()
    _optional_parameters = ()
    _output_parameters = ()
    _mandatory_creds_parameters = ()
    _optional_creds_parameters = ()

    def __init__(self, **kwargs):
        # I care only about the parameters set on ~self._parameters
        self._credentials = {}
        params = {k for k, v in kwargs.items()}\
            .intersection({'{}{}'.format(self.__provider_prefix__, k) for k in self._mandatory_parameters})
        for k, v in kwargs.items():
            if k in params:
                setattr(self, k, v)

    def __str__(self):
        return '<Provider: %s>' % self.__provider_name__

    @classmethod
    def name(cls):
        """Return the provider name."""
        return cls.__provider_name__

    @property
    def credentials(self):
        """Return the credentials for the provider."""
        return self._credentials

    @credentials.setter
    def credentials(self, value):
        """Raise an exception when trying to set the credentials for the
        provider after the class has been instanciated. You should use the
        set_credentials method to set credentials.
        :param value: The provider credentials
        """
        raise ValueError('You cannot set provider credentials directly. Use '
                         'function ~CarbonProvider.set_credentials')

    def set_credentials(self, cdata):
        """Set the provider credentials.
        :param cdata: The provider credentials dict
        """
        for p in self.get_mandatory_creds_parameters():
            self._credentials[p] = cdata[p]

        for p in self.get_optional_creds_parameters():
            if p in cdata:
                self._credentials[p] = cdata[p]

    @classmethod
    def check_mandatory_parameters(cls, parameters):
        """
        Validates the parameters against the mandatory parameters set
        by the class.
        :param parameters: a dictionary of parameters
        :return: an empty set if all mandatory fields satisfy or the list of
                 fields that needs to be filled.
        """
        intersec = {k for k, v in parameters.items()}\
            .intersection({'{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters})
        return {'{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters}.difference(intersec)

    @classmethod
    def check_mandatory_creds_parameters(cls, parameters):
        """
        Validates the parameters against the mandatory credentials parameters
        set by the class.
        :param parameters: a dictionary of parameters
        :return: an empty set if all mandatory creds fields satisfy or the list
                 of fields that needs to be filled.
        """
        intersec = {k for k, v in parameters.items()}\
            .intersection({k for k in cls._mandatory_creds_parameters})
        return {k for k in cls._mandatory_creds_parameters}.difference(intersec)

    @classmethod
    def get_mandatory_creds_parameters(cls):
        """
        Get the list of the mandatory credential parameters
        :return: a tuple of the mandatory credential paramaters.
        """
        return (k for k in cls._mandatory_creds_parameters)

    @classmethod
    def get_optional_creds_parameters(cls):
        """Get the list of the optional credential parameters.
        :return: A tuple of the optional credential parameters.
        """
        return (k for k in cls._optional_creds_parameters)

    @classmethod
    def get_mandatory_parameters(cls):
        """
        Get the list of the mandatory parameters
        :return: a tuple of the mandatory paramaters.
        """
        return ('{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters)

    @classmethod
    def get_optional_parameters(cls):
        """
        Get the list of the optional parameters
        :return: a tuple of the optional paramaters.
        """
        return ('{}{}'.format(cls.__provider_prefix__, k) for k in cls._optional_parameters)

    @classmethod
    def get_all_parameters(cls):
        """
        Return the list of all possible parameters for the provider.
        :return: a tuple with all parameters
        """
        all_params = {'{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters} \
            .union({'{}{}'.format(cls.__provider_prefix__, k) for k in cls._optional_parameters},
                   {'{}{}'.format(cls.__provider_prefix__, k) for k in cls._output_parameters})
        return (param for param in all_params)

    @classmethod
    def is_optional(cls, value):
        return value in cls.get_optional_parameters()

    @classmethod
    def is_mandatory(cls, value):
        return value in cls.get_mandatory_parameters()

    def validate(self, host):
        """
        Run a validation for all validate_<param_name> that is
        found in the provider class.
        :param host: the Host object to which the validation is run for
        :return: list of invalid parameters
        """
        # collect the host paramaters and its validate functions
        try:
            # This generator goes through all provider parameters
            # and generate a list of tuples of each holds the host
            # parameter and the provider function that validates the
            # host parameter. For example, for Openstack Provider:
            #
            # items = [
            #   ('host.os_image', 'provider.validate_image()'),
            #   ('host.os_flavor', 'provider.validate_flavor()'),
            # ]
            #
            # It then returns the list of parameters that the validate
            # functions will return false.
            #
            # It throws an CarbonProviderException if the host doesn't have the
            # attribute to be validated or if the provider has not implemented
            # the validate_<param> function.
            items = [
                (param,
                 getattr(host, '{}{}'.format(self.__provider_prefix__, param)),
                 getattr(self, "validate_%s" % param),)
                for param in (self._mandatory_parameters + self._optional_parameters)]
            return [(param, value) for param, value, func in [item for item in items] if not func(value)]
        except AttributeError as e:
            raise CarbonProviderException(e.args[0])

    @classmethod
    def build_profile(cls, host):
        """
        Builds a dictionary with with all parameters for the provider
        :param host: a Host object
        :return: a dictionary with all parameters
        """
        profile = {}
        for param in cls.get_all_parameters():
            profile.update({
                param: getattr(host, param, None)
            })
        return profile


class CarbonController(LoggerMixin):
    """This is the base class for all controllers.

    Every controller will need to inherit the carbon controller. Controllers
    handle actions between carbon and its resources aka hosts.
    """

    __controller_name__ = None

    def __init__(self):
        """Constructor."""
        pass

    @property
    def name(self):
        """Return the name of the controller."""
        return self.__controller_name__

    @name.setter
    def name(self, value):
        """Raises an exception when trying to set controller name property.

        :param value: Name of controller to set.
        """
        raise ValueError('You cannot set the controller name property.')
