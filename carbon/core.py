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
import errno
import inspect
from collections import namedtuple
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging import Formatter, getLogger, StreamHandler, FileHandler
from time import time

import os

from .constants import TASKLIST
from .helpers import fetch_hosts, get_core_tasks_classes
#from .signals import (
#    provision_create_started, provision_create_finished,
#    provision_delete_started, provision_delete_finished
#)


class CarbonError(Exception):
    """Carbon's base Exception class"""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        self.message = message
        super(CarbonError, self).__init__(message)


class CarbonTaskError(CarbonError):
    """Carbon's task base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonTaskError, self).__init__(message)


class CarbonResourceError(CarbonError):
    """Carbon's resource base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonResourceError, self).__init__(message)


class CarbonProvisionerError(CarbonError):
    """Carbon's provisioner base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonProvisionerError, self).__init__(message)


class CarbonProviderError(CarbonError):
    """Carbon's provider base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonProviderError, self).__init__(message)


class CarbonOrchestratorError(CarbonError):
    """Carbon's orchestrator base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(CarbonOrchestratorError, self).__init__(message)


class LoggerMixinError(CarbonError):
    """Carbon's logger mixin base exception class."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        super(LoggerMixinError, self).__init__(message)


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
    def create_logger(cls, name, config=None):
        """Create logger.

        This method will create logger's to be used throughout carbon.

        :param name: Name for the logger to create.
        :type name: str
        :param config: Carbon config object.
        :type config: dict
        """
        # get logger
        logger = getLogger(name)

        # skip creating logger if handler already exists
        if len(logger.handlers) > 0:
            return

        # construct stream handler
        stream_handler = StreamHandler()

        # create log directory
        log_dir = os.path.join(config['DATA_FOLDER'], 'logs')

        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except OSError as ex:
            msg = 'Unable to create %s directory' % log_dir
            if ex.errno == errno.EACCES:
                msg += ', permission defined.'
            else:
                msg += ', %s.' % ex
            raise LoggerMixinError(msg)

        # construct file handler
        file_handler = FileHandler(os.path.join(
            log_dir, 'carbon_scenario.log'))

        # configure handlers
        for handler in [stream_handler, file_handler]:
            handler.setLevel(cls._LOG_LEVELS[config['LOG_LEVEL']])
            handler.setFormatter(Formatter(cls._LOG_FORMAT))

        # configure logger
        logger.setLevel(cls._LOG_LEVELS[config['LOG_LEVEL']])
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    @property
    def logger(self):
        """Returns the default logger (carbon logger) object."""
        return getLogger(inspect.getmodule(inspect.stack()[1][0]).__name__)


class TimeMixin(object):
    """Carbon's time mixin class.

    This class provides an easy interface for other carbon classes to save
    a start and end time. Once times are saved they can calculate the time
    delta between the two points in time.
    """
    _start_time = None
    _end_time = None
    _hours = 0
    _minutes = 0
    _secounds = 0

    def start(self):
        """Set the start time."""
        self._start_time = time()

    def end(self):
        """Set the end time."""
        self._end_time = time()

        # calculate time delta
        delta = self._end_time - self._start_time
        self.hours = delta // 3600
        delta = delta - 3600 * self.hours
        self.minutes = delta // 60
        self.seconds = delta - 60 * self.minutes

    @property
    def start_time(self):
        """Return the start time."""
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        """Set the start time.

        :param value: Start time.
        :type value: int
        """
        raise CarbonError('You cannot set the start time.')

    @property
    def end_time(self):
        """Return the end time."""
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        """Set the end time.

        :param value: End time.
        :type value: int
        """
        raise CarbonError('You cannot set the end time.')

    @property
    def hours(self):
        """Return hours."""
        return self._hours

    @hours.setter
    def hours(self, value):
        """Set hours.

        :param value: Hours to set.
        :type value: int
        """
        self._hours = value

    @property
    def minutes(self):
        """Return minutes."""
        return self._minutes

    @minutes.setter
    def minutes(self, value):
        """Set minutes.

        :param value: Minutes to set.
        :type value: int
        """
        self._minutes = value

    @property
    def seconds(self):
        """Return seconds."""
        return self._secounds

    @seconds.setter
    def seconds(self, value):
        """Set seconds.

        :param value: Seconds to set.
        :type value: int
        """
        self._secounds = value


class CarbonTask(LoggerMixin, TimeMixin):
    """
    This is the base class for every task created for Carbon framework.
    All instances of this class can be found within the ~carbon.tasks
    package.
    """

    __task_name__ = None
    __concurrent__ = True

    def __init__(self, name=None, **kwargs):
        if name is not None:
            self.name = name

    def run(self):
        pass

    def __str__(self):
        return self.name


class CarbonResource(LoggerMixin, TimeMixin):
    """
    This is the base class for every resource created for Carbon Framework.
    All instances of this class can be found within ~carbon.resources
    package.
    """
    _valid_tasks_types = []
    _req_tasks_methods = ['run']
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
            raise CarbonResourceError(
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


class CarbonProvisioner(LoggerMixin, TimeMixin):
    """
    This is the base class for all provisioners for provisioning machines
    """
    __provisioner_name__ = None
    host = None

    def _create(self):
        raise NotImplementedError

    def create(self):
        #provision_create_started.send(self, host=self.host)
        self._create()
        #provision_create_finished.send(self, host=self.host)

    def _delete(self):
        raise NotImplementedError

    def delete(self):
        #provision_delete_started.send(self, host=self.host)
        self._delete()
        #provision_delete_finished.send(self, host=self.host)

    @property
    def name(self):
        """Return the name for the provisioner."""
        return self.__provisioner_name__

    @name.setter
    def name(self, value):
        """
        Returns the name of the provisioner
        :param value: The name for the provisioner.
        """
        raise AttributeError('You cannot set name for the provisioner.')


class CarbonProvider(LoggerMixin, TimeMixin):
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

    # all parameters that MUST be set for the provider
    _mandatory_parameters = ()

    # additional parameters that can be set for the provider
    _optional_parameters = ()

    # parameters that will be set based on output of the provider
    # for instance, for the Openstack, ip_address and for Openshift
    # routes
    _output_parameters = ()

    # all credential parameters that MUST be set for the provider's credential
    _mandatory_creds_parameters = ()

    # additional parameters that can be set for the provider's credential
    _optional_creds_parameters = ()

    # special parameters that contain file paths - assets parameters must
    # be added to either mandatory or optional.
    _assets_parameters = ()

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

    @property
    def name(self):
        """Return the provider name."""
        return self.__provider_name__

    @name.setter
    def name(self, value):
        """Raises an exception when trying to set the name for the provider
        :param value: name
        """
        raise AttributeError('You cannot set provider name.')

    @property
    def prefix(self):
        """Return the provider prefix"""
        return self.__provider_prefix__

    @prefix.setter
    def prefix(self, value):
        """Raises an exception when trying to set the provider prefix
        :param value: prefix
        """
        raise AttributeError('You cannot set provider prefix.')

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
            else:
                self._credentials[p] = None

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
            .intersection(cls._mandatory_parameters_set())

        return cls._mandatory_parameters_set().difference(intersec)

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
            .intersection({k for k in cls.get_mandatory_creds_parameters()})
        return {k for k in cls.get_mandatory_creds_parameters()}.difference(intersec)

    @classmethod
    def _mandatory_parameters_set(cls):
        """
        Build a set of mandatory parameters
        :return: a set
        """
        return {'{}{}'.format(cls.__provider_prefix__, k) for k in cls._mandatory_parameters}

    @classmethod
    def get_mandatory_parameters(cls):
        """
        Get the list of the mandatory parameters
        :return: a tuple of the mandatory parameters.
        """
        return (param for param in cls._mandatory_parameters_set())

    @classmethod
    def _mandatory_creds_parameters_set(cls):
        """
        Build a set of mandatory parameters
        :return: a set
        """
        return {k for k in cls._mandatory_creds_parameters}

    @classmethod
    def get_mandatory_creds_parameters(cls):
        """
        Get the list of the mandatory credential parameters
        :return: a tuple of the mandatory parameters.
        """
        return (param for param in cls._mandatory_creds_parameters_set())

    @classmethod
    def _optional_creds_parameters_set(cls):
        """
        Build a set of optional parameters
        :return: a set
        """
        return {k for k in cls._optional_creds_parameters}

    @classmethod
    def get_optional_creds_parameters(cls):
        """
        Get the list of the optional credential parameters
        :return: a tuple of the optional parameters.
        """
        return (param for param in cls._optional_creds_parameters_set())

    @classmethod
    def _optional_parameters_set(cls):
        """
        Build a set of optional parameters
        :return: a set
        """
        return {'{}{}'.format(cls.__provider_prefix__, k) for k in cls._optional_parameters}

    @classmethod
    def get_optional_parameters(cls):
        """
        Get the list of the optional parameters
        :return: a tuple of the optional parameters.
        """
        return (param for param in cls._optional_parameters_set())

    @classmethod
    def _all_parameters_set(cls):
        """
        Build a set of all parameters
        :return: a set
        """
        return cls._mandatory_parameters_set()\
            .union(cls._optional_parameters_set())

    @classmethod
    def get_all_parameters(cls):
        """
        Return the list of all possible parameters for the provider.
        :return: a tuple with all parameters
        """
        return (param for param in cls._all_parameters_set())

    @classmethod
    def _all_creds_parameters_set(cls):
        """
        Build a set of all credential parameters
        :return: a set
        """
        return cls._mandatory_creds_parameters_set()\
            .union(cls._optional_creds_parameters_set())

    @classmethod
    def get_all_creds_parameters(cls):
        """
        Return the list of all possible credential parameters for
        the provider.
        :return: a tuple
        """
        return (param for param in cls._all_creds_parameters_set())

    @classmethod
    def _assets_parameters_set(cls):
        """
        Build a set of assets parameters from the
        intersection between all parameters and what
        it is in the `cls._assets_parameters`
        :return: a set
        """
        return cls._all_parameters_set().intersection(
            {'{}{}'.format(cls.__provider_prefix__, k)
             for k in cls._assets_parameters}
        )

    @classmethod
    def _assets_creds_parameters_set(cls):
        """
        Build a set of assets parameters from the
        intersection between all parameters and what
        it is in the `cls._assets_parameters`
        :return: a set
        """
        return cls._all_creds_parameters_set().intersection(
            {k for k in cls._assets_parameters}
        )

    @classmethod
    def get_assets_parameters(cls):
        """
        Get the list of the assets parameters
        :return: a tuple
        """
        all_assets = cls._assets_parameters_set()\
            .union(cls._assets_creds_parameters_set())

        return (param for param in all_assets)

    @classmethod
    def _output_parameters_set(cls):
        """
        Build a set of output parameters from the
        intersection between all parameters and what
        it is in the `cls._assets_parameters`
        :return: a set
        """
        return cls._all_parameters_set().intersection(
            {'{}{}'.format(cls.__provider_prefix__, k)
             for k in cls._output_parameters}
        )

    @classmethod
    def get_output_parameters(cls):
        """
        Get the list of the output parameters
        :return: a tuple
        """
        return (param for param in cls._output_parameters_set())

    @classmethod
    def is_optional(cls, value):
        return value in cls.get_optional_parameters()

    @classmethod
    def is_mandatory(cls, value):
        return value in cls.get_mandatory_parameters()

    @classmethod
    def is_asset(cls, value):
        return value in cls.get_assets_parameters()

    @classmethod
    def is_credential_asset(cls, value):
        return value in cls.get_assets_creds_parameters()

    @classmethod
    def is_output(cls, value):
        return value in cls.get_output_parameters()

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
            # It throws an CarbonProviderError if the host doesn't have the
            # attribute to be validated or if the provider has not implemented
            # the validate_<param> function.
            items = [
                (param,
                 getattr(host, '{}{}'.format(self.__provider_prefix__, param)),
                 getattr(self, "validate_%s" % param),)
                for param in (self._mandatory_parameters + self._optional_parameters)]
            return [(param, value) for param, value, func in [item for item in items] if not func(value)]
        except AttributeError as e:
            raise CarbonProviderError(e.args[0])

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


class CarbonOrchestrator(LoggerMixin, TimeMixin):

    __orchestrator_name__ = None

    # orchestrator assets may be files that are needed for remote connections
    # such as SSH keys, etc
    _assets_parameters = ()

    def __init__(self, action=None, hosts=None, **kwargs):
        """Constructor."""
        self._action = action
        self._hosts = hosts

        # set all other attributes
        for k, v in kwargs.items():
            setattr(self, k, v)

    def validate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    @property
    def name(self):
        """Return the name of the orchestrator."""
        return self.__orchestrator_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the orchestrator.')

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        raise AttributeError('You cannot set the action the orchestrator will'
                             ' perform.')

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        # TODO: reword
        raise AttributeError('You cannot set the hosts for the action after'
                             'object is created.')


class PipelineBuilder(object):
    """Carbon's pipeline builder.

    The primary purpose of this class is to dynamically build pipelines at
    carbon run time.
    """
    # A pipeline is a tuple with a name, type and a list of tasks.
    # The Carbon object will have a list of pipelines that holds
    # all types of pipelines and a list of tasks associated with the
    # type of the pipeline.
    pipeline_template = namedtuple('Pipeline', ('name', 'type', 'tasks'))

    def __init__(self, name):
        """Constructor.

        :param name: Pipeline name.
        :type name: str
        """
        self._name = name

    @property
    def name(self):
        """Return the pipeline name"""
        return self._name

    def is_task_valid(self):
        """Check if the pipeline task name is valid for carbon.

        :return: Whether task is valid or not.
        :rtype: bool
        """
        try:
            TASKLIST.index(self.name)
        except ValueError:
            return False
        return True

    def task_cls_lookup(self):
        """Lookup the pipeline task class type.

        :return: The class associated for the pipeline task.
        :rtype: class
        """
        for cls in get_core_tasks_classes():
            if cls.__task_name__ == self.name:
                return cls
        raise CarbonError('Unable to lookup task %s class.' % self.name)

    def build(self, scenario):
        """Build carbon pipeline.

        :param scenario: Carbon scenario object containing all scenario
            data.
        :type scenario: object
        :return: Carbon pipeline to run for the given task.
        :rtype: tuple
        """
        # initialize new pipeline
        pipeline = self.pipeline_template(
            self.name,
            self.task_cls_lookup(),
            list()
        )

        # RFE: consolidate configuring pipeline to reduce code duplication

        # resource = scenario
        for task in scenario.get_tasks():
            if task['task'].__task_name__ == self.name:
                pipeline.tasks.append(task)

        # resource = host
        for host in scenario.hosts:
            for task in host.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        # resource = action
        for action in scenario.actions:
            for task in action.get_tasks():
                if task['task'].__task_name__ == self.name:
                    # fetch & set hosts for the given action task
                    task = fetch_hosts(scenario.hosts, task)
                    pipeline.tasks.append(task)

        # resource = execute
        for execute in scenario.executes:
            for task in execute.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        # resource = report
        for report in scenario.reports:
            for task in report.get_tasks():
                if task['task'].__task_name__ == self.name:
                    pipeline.tasks.append(task)

        return pipeline
