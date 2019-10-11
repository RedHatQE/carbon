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

    Module containing the core classes which carbon resources, tasks,
    providers, provisioners, etc inherit.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import errno
import inspect
import os
from glob import glob
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging import Formatter, getLogger, StreamHandler, FileHandler, LoggerAdapter, Filter
from time import time, sleep
from collections import OrderedDict

from .exceptions import CarbonError, CarbonResourceError, LoggerMixinError, \
    CarbonProvisionerError, CarbonImporterError
from .helpers import get_core_tasks_classes
from traceback import format_exc
from ._compat import RawConfigParser
from uuid import uuid4
from sys import exc_info


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

        class Asset(CarbonResource):
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

    _DEBUG_LOG_FORMAT = ("%(asctime)s %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")
    _INFO_LOG_FORMAT = ("%(asctime)s %(levelname)s %(message)s")

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
            # remove the extra logging regarding class/function/lineno if not in debug mode
            if config['LOG_LEVEL'] == 'info':
                handler.setFormatter(Formatter(cls._INFO_LOG_FORMAT))
            else:
                handler.setFormatter(Formatter(cls._DEBUG_LOG_FORMAT))

        # add exception filter to the stream handler so we don't print stack trace
        filter = LoggerMixin.ExceptionFilter()
        stream_handler.addFilter(filter)

        # configure logger
        logger.setLevel(cls._LOG_LEVELS[config['LOG_LEVEL']])
        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    @property
    def logger(self):
        """Returns the default logger (carbon logger) object."""
        return getLogger(inspect.getmodule(inspect.stack()[1][0]).__name__)

    class ExceptionFilter(Filter):

        def filter(self, record):
            if record.getMessage().find('Traceback') != -1:
                return False
            else:
                return True


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


class FileLockMixin(object):
    """
    The FileLockMixin is designed to
    use file locks to be able to read/write
    to a file when multipleprocesses need to
    access the same file.
    """
    _lock_file = '/tmp/cbn.lock'
    _lock_sleep = 5
    _lock_timeout = 120

    @property
    def lock_file(self):
        return self._lock_file

    @lock_file.setter
    def lock_file(self, value):
        self._lock_file = value

    @property
    def lock_sleep(self):
        return self._lock_sleep

    @lock_sleep.setter
    def lock_sleep(self, value):
        self._lock_sleep = value

    @property
    def lock_timeout(self):
        return self._lock_timeout

    @lock_timeout.setter
    def lock_timeout(self, value):
        self._lock_timeout = value

    def acquire(self):
        self.cleanup_locks()
        if self._check_and_sleep():
            open(self._lock_file, 'w').close()

    def release(self):
        try:
            os.remove(self._lock_file)
        except OSError:
            raise

    def _check_and_sleep(self):

        attempts = 0
        total_attempts = self.lock_timeout / self.lock_sleep

        while os.path.exists(self.lock_file):
            if attempts < total_attempts:
                sleep(self.lock_sleep)
                attempts += 1
            else:
                raise CarbonError('Timed out waiting for the lock to release')
        return True

    def cleanup_locks(self):
        if glob(os.path.join(os.path.dirname(self.lock_file), 'cbn*')):
            for f in glob(os.path.join(os.path.dirname(self.lock_file), 'cbn*')):
                if f != self.lock_file:
                    os.remove(f)


class CarbonTask(LoggerMixin, TimeMixin):
    """
    This is the base class for every task created for Carbon framework.
    All instances of this class can be found within the ~carbon.tasks
    package.
    """

    __task_name__ = None
    __concurrent__ = True
    __task_id__ = ''

    def __init__(self, name=None, **kwargs):
        if name is not None:
            self.name = name

    def run(self):
        pass

    def __str__(self):
        return self.name

    @staticmethod
    def get_formatted_traceback():
        """Get traceback when exception is raised. Will log traceback as well.
        :return: Exception information.
        :rtype: tuple
        """

        return format_exc()


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

        # every resource can have a optional description
        self._description = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        raise AttributeError('You can set name after class is instantiated.')

    @property
    def config(self):
        return self._config

    @config.setter
    def config(self, value):
        raise AttributeError('You can set config after resource is created.')

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        raise AttributeError('You cannot set the resource description after '
                             'its class is instantiated.')

    @property
    def workspace(self):
        """Scenario workspace property.

        :return: scenario workspace folder
        :rtype: str
        """
        return str(self.config['WORKSPACE'])

    @workspace.setter
    def workspace(self, value):
        """Set workspace."""
        raise AttributeError('You cannot set the workspace directly. Only '
                             'the carbon object can.')

    @property
    def data_folder(self):
        """Data folder property.

        :return: resource data folder
        :rtype: str
        """
        return str(self.config['DATA_FOLDER'])

    @data_folder.setter
    def data_folder(self, value):
        """Set data folder."""
        raise AttributeError('You cannot set the data folder directly. Only '
                             'the carbon object can.')

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
            elif key == 'description':
                self._description = value
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
    """Carbon provisioner class.

    Each provisioner implementation added into carbon requires that they
    inherit the carbon provisioner class. This enforces that the
    required methods are implemented in the new provisioner class.
    """
    # set the provisioner name
    __provisioner_name__ = None

    def __init__(self, host):
        """Constructor.

        Every provisioner requires a carbon host resource. This resource
        contains all the necessary elements that are needed to fulfill a
        provision request by the provisioner of choice.

        :param host: carbons host resource
        :type host: object
        """
        self.host = host

        # set commonly accessed data used by provisioners
        self.data_folder = getattr(self.host, 'data_folder')
        self.provider = getattr(getattr(host, 'provider'), 'name')
        self.provider_params = getattr(host, 'provider_params')
        self.provider_credentials = getattr(getattr(
            host, 'provider'), 'credentials')
        self.workspace = getattr(self.host, 'workspace')

        if not self.name and self.__class__.__name__ != 'CarbonProvisioner':
            raise CarbonProvisionerError(
                'Attribute __provisioner_name__ is None. Please set the '
                'attribute and retry creating an object from the class.'
            )

    def create(self):
        """Create method.

        Main entry point for the provisioner to fulfill a provision request for
        machines. Carbons provision task invokes the provisioners create
        method to create all test machines.
        """
        raise NotImplementedError

    def delete(self):
        """Delete method.

        Main entry point for the provisioner to fulfill the request to delete
        machines. Carbons cleanup task invokes the provisioners delete method
        to delete all test machines.
        """
        raise NotImplementedError

    @property
    def name(self):
        """Return the name for the provisioner."""
        return self.__provisioner_name__

    @name.setter
    def name(self, value):
        """Set the provisioner name.

        :param value: provisioner name
        :type value: str
        """
        raise AttributeError('You cannot set name for the provisioner.')


class CarbonProvider(LoggerMixin, TimeMixin):
    """Carbon Provider."""
    __provider_name__ = None

    def __init__(self):
        """Constructor."""
        self._req_params = []
        self._opt_params = []
        self._req_credential_params = []
        self._opt_credential_params = []
        self._credentials = {}

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
    def req_params(self):
        """Return the required parameters."""
        return self._req_params

    @req_params.setter
    def req_params(self, value):
        """Set the required parameters."""
        self._req_params.extend(value)

    @property
    def opt_params(self):
        """Return the optional parameters."""
        return self._opt_params

    @opt_params.setter
    def opt_params(self, value):
        """Set the optional parameters."""
        self._opt_params.extend(value)

    @property
    def req_credential_params(self):
        """Return the required credential parameters."""
        return self._req_credential_params

    @req_credential_params.setter
    def req_credential_params(self, value):
        """Set the required credential parameters."""
        self._req_credential_params.extend(value)

    @property
    def opt_credential_params(self):
        """Return the optional credential parameters."""
        return self._opt_credential_params

    @opt_credential_params.setter
    def opt_credential_params(self, value):
        """Set the optional credential parameters."""
        self._opt_credential_params.extend(value)

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
        for p in self.req_credential_params:
            param = p[0]
            self._credentials[param] = cdata[param]

        for p in self.opt_credential_params:
            param = p[0]
            if param in cdata:
                self._credentials[param] = cdata[param]

    def validate_req_params(self, resource):
        """Validate the required parameters exists in the host resource.

        :param host: host resource
        :type host: object
        """
        for item in self.req_params:
            name = getattr(resource, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : required param '%s' " % (name, param)
            try:
                param_value = getattr(resource, 'provider_params')[param]
                self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )
            except KeyError:
                msg = msg + 'does not exist.'
                self.logger.error(msg)
                raise CarbonError(msg)

    def validate_opt_params(self, resource):
        """Validate the optional parameters exists in the host resource.

        :param resource: host resource
        :type resource: object
        """
        for item in self.opt_params:
            name = getattr(resource, 'name')
            param, param_type = item[0], item[1]
            msg = "Asset %s : optional param '%s' " % (name, param)
            try:
                param_value = getattr(resource, 'provider_params')[param]
                self.logger.info(msg + 'exists.')

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type))
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )
            except KeyError:
                self.logger.warning(msg + 'is undefined for resource.')

    def validate_req_credential_params(self, resource):
        """Validate the required credential parameters exists in the host.

        :param resource: host resource
        :type resource: object
        """
        for item in self.req_credential_params:
            name = getattr(resource, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : required credential param '%s' " % (name, param)
            try:
                provider = getattr(resource, 'provider')
                param_value = getattr(provider, 'credentials')[param]
                if param_value:
                    self.logger.info(msg + 'exists.')
                else:
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )

                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Required Type=%s. (ERROR)' %
                        (type(param_value), param_type)
                    )
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resource, 'name')
                    )
            except (AttributeError, KeyError):
                msg = msg + 'does not exist.'
                self.logger.error(msg)
                raise CarbonError(msg)

    def validate_opt_credential_params(self, resources):
        """Validate the optional credential parameters exists in the host.

        :param resources: host resource
        :type resources: object
        """
        for item in self.opt_credential_params:
            name = getattr(resources, 'name')
            param, param_type = item[0], item[1]
            msg = "Resource %s : optional credential param '%s' " % (name, param)
            try:
                provider = getattr(resources, 'provider')
                param_value = getattr(provider, 'credentials')[param]
                if param_value:
                    self.logger.info(msg + 'exists.')
                else:
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resource %s' % getattr(resources, 'name')
                    )
                if not type(param_value) in param_type:
                    self.logger.error(
                        '    - Type=%s, Optional Type=%s. (ERROR)' %
                        (type(param_value), param_type)
                    )
                    raise CarbonError(
                        'Error occurred while validating required provider '
                        'parameters for resources %s' % getattr(resources, 'name')
                    )
            except (AttributeError, KeyError):
                self.logger.warning(msg + 'does not exist.')


class CloudProvider(CarbonProvider):
    """Cloud provider class."""
    def __init__(self):
        super(CloudProvider, self).__init__()
        """Constructor."""
        self._req_params = [
            ('name', [str]),
            ('image', [str]),
            ('flavor', [str]),
            ('networks', [list])
        ]
        self._opt_params = [
            ('hostname', [str])
        ]


class PhysicalProvider(CarbonProvider):
    """Physical provider class."""
    def __init__(self):
        super(PhysicalProvider, self).__init__()
        """Constructor."""
        pass


class ReportProvider(CarbonProvider):
    """Report provider class."""
    def __init__(self):
        super(ReportProvider, self).__init__()
        """Constructor."""
        pass


class CarbonOrchestrator(LoggerMixin, TimeMixin):

    __orchestrator_name__ = None

    # all parameters that MUST be set for the orchestrator
    _mandatory_parameters = ()

    # additional parameters that can be set for the orchestrator
    _optional_parameters = ()

    def __init__(self):
        """Constructor."""
        self._action = None
        self._hosts = None
        self._status = 0

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
        raise AttributeError('Hosts cannot be set once the object is created.')

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @classmethod
    def _mandatory_parameters_set(cls):
        """
        Build a set of mandatory parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__orchestrator_name__, k) for k in cls._mandatory_parameters}

    @classmethod
    def get_mandatory_parameters(cls):
        """
        Get the list of the mandatory parameters
        :return: a tuple of the mandatory parameters.
        """
        return (param for param in cls._mandatory_parameters_set())

    @classmethod
    def _optional_parameters_set(cls):
        """
        Build a set of optional parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__orchestrator_name__, k) for k in cls._optional_parameters}

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
    def build_profile(cls, action):
        """Builds a dictionary with all the parameters for the orchestrator.

        :param action: action object
        :type action: object
        :return: dictionary with all orchestrator parameters
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        for param in cls.get_all_parameters():
            profile.update({param: getattr(action, param, None)})
        return profile


class CarbonExecutor(LoggerMixin, TimeMixin):

    __executor_name__ = None

    # all parameters that MUST be set for the executor
    _mandatory_parameters = ()

    # additional parameters that can be set for the executor
    _optional_parameters = ()

    # execute types the executor offers
    _execute_types = []

    def __init__(self, execute=None, host=None):
        """Constructor."""
        self._execute = execute
        self._hosts = host

    def validate(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    @property
    def name(self):
        """Return the name of the executor."""
        return self.__executor_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the executor.')

    @property
    def execute(self):
        return self._execute

    @execute.setter
    def execute(self, value):
        raise AttributeError('You cannot set the execute to run.')

    @property
    def hosts(self):
        return self._hosts

    @hosts.setter
    def hosts(self, value):
        raise AttributeError('Hosts cannot be set once the object is created.')

    @classmethod
    def _mandatory_parameters_set(cls):
        """
        Build a set of mandatory parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__executor_name__, k) for k in cls._mandatory_parameters}

    @classmethod
    def get_mandatory_parameters(cls):
        """
        Get the list of the mandatory parameters
        :return: a tuple of the mandatory parameters.
        """
        return (param for param in cls._mandatory_parameters_set())

    @classmethod
    def _optional_parameters_set(cls):
        """
        Build a set of optional parameters
        :return: a set
        """
        return {'{}_{}'.format(cls.__executor_name__, k) for k in cls._optional_parameters}

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
    def build_profile(cls, execute):
        """Builds a dictionary with all the parameters for the executor.

        :param execute: execute object
        :type execute: object
        :return: dictionary with all executor parameters
        :rtype: OrderedDict
        """
        profile = OrderedDict()
        for param in cls.get_all_parameters():
            profile.update({param: getattr(execute, param, None)})
        return profile


class CarbonImporter(LoggerMixin, TimeMixin):

    # set the importer name
    __importer_name__ = None

    def __init__(self, report):
        """Constructor.

        The reporter requires a carbon report resource. This resource
        contains all the necessary elements that are needed to fulfill
        the reporting request by the reporter of choice.

        :param report: carbons report resource
        :type report: object
        """
        self._report = report

        # set commonly accessed data used by importers
        self.report_name = getattr(report, 'name')
        self.data_folder = getattr(report, 'data_folder')
        self.provider = getattr(getattr(report, 'provider'), 'name', 'dummy')
        self.provider_params = getattr(report, 'provider_params', {})
        self.provider_credentials = getattr(getattr(
            report, 'provider'), 'credentials', {})
        self.workspace = getattr(report, 'workspace')
        self.config = getattr(report, 'config')

        if not self.name and self.__class__.__name__ != 'CarbonImporter':
            raise CarbonImporterError(
                'Attribute __importer_name__ is None. Please set the '
                'attribute and retry creating an object from the class.'
            )

    @property
    def name(self):
        """Return the name of the importer."""
        return self.__importer_name__

    @name.setter
    def name(self, value):
        raise AttributeError('You cannot set name for the importer.')

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, value):
        raise AttributeError('You cannot set the report to run.')

    def import_artifacts(self):
        raise NotImplementedError

    def cleanup_artifacts(self):
        raise NotImplementedError

    def aggregate_artifacts(self):
        raise NotImplementedError

    def validate_artifacts(self):
        raise NotImplementedError


class CarbonPlugin(LoggerMixin, TimeMixin):
    """Carbon gateway class.

        Base class that all carbon resource implmentations will use. This
        is to facilitate decoupling the interface from the implementation.
        """
    # set the plugin name
    __plugin_name__ = None


class ProvisionerPlugin(CarbonPlugin):
    """Carbon provisioner plugin class.

    Each provisioner implementation added into carbon requires that they
    inherit the carbon provisioner class. This enforces that the
    required methods are implemented in the new provisioner class.
    Additional support/helper methods can be added to this class
    """

    def __init__(self, host):

        """Constructor.

        Each host resource is linked to a provider which is the location where
        the host will be provisioned. Along with the provider you will also
        have access to all the provider parameters needed to fulfill the
        provision request. (i.e. images, flavor, network, etc. depending on
        the provider).

        Common Attributes:
          - name: data_folder
            description: the runtime folder where all files/results are stored
            and archived for historical purposes.
            type: string

          - name: provider
            description: name of the provider where host is to be created or
            deleted.
            type: string

          - name: provider_params
            description: available data about the host to be created or
            deleted in the provider defined.
            type: dictionary

          - name: provider_credentials
            description: credentials for the provider associated to the host
            resource.
            type: dictionary

          - name: workspace
            description: workspace where carbon can access all files needed
            by the scenario in order to successfully run it.
            type: string

        There can be more information within the host resource but the ones
        defined above are the most commonly ones used by provisioners.

        :param host: carbon host resource
        :type host: object
        """

        self.host = host

        # set commonly accessed data used by provisioners
        self.data_folder = getattr(self.host, 'data_folder')
        self.provider = getattr(getattr(host, 'provider'), 'name')
        self.provider_params = getattr(host, 'provider_params')
        self.provider_credentials = getattr(getattr(
            host, 'provider'), 'credentials')
        self.workspace = getattr(self.host, 'workspace')

    def create(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def authenticate(self):
        raise NotImplementedError


class ImporterPlugin(CarbonPlugin):
    """Carbon reporter plugin class.

    Each reporter implementation added into carbon requires that they
    inherit the carbon reporter plugin class. This enforces that the
    required methods are implemented in the new plugin class.
    Additional support/helper methods can be added to this class.
    """

    def __init__(self, profile):

        self.profile = profile

        # set commonly accessed data used by the importer
        self.data_folder = self.profile['data_folder']
        self.provider = self.profile['provider']['name']
        self.provider_params = self.profile['provider']
        self.provider_credentials = self.profile['provider_credentials']
        self.workspace = self.profile['workspace']
        self.artifacts = self.profile['artifacts']
        self.import_results = []
        self.config_params = self.profile['config_params']

    def aggregate_artifacts(self):
        raise NotImplementedError

    def import_artifacts(self):
        raise NotImplementedError

    def cleanup_artifacts(self):
        raise NotImplementedError


class OrchestratorPlugin(CarbonPlugin):
    """Carbon orchestrator gateway class.

    Each orchestrator implementation added into carbon requires that they
    inherit the carbon orchestrator plugin class. This enforces that the
    required methods are implemented in the new plugin class.
    Additional support/helper methods can be added to this class.
    """

    def __init__(self):
        pass

    def run(self):
        raise NotImplementedError


class ExecutorPlugin(CarbonPlugin):
    """Carbon executor plugin class.

    Each executor implementation added into carbon requires that they
    inherit the carbon executor plugin class. This enforces that the
    required methods are implemented in the new plugin class.
    Additional support/helper methods can be added to this class.
    """

    def __init__(self):
        pass

    def run(self):
        raise NotImplementedError


class Inventory(LoggerMixin, FileLockMixin):
    """Inventory.

    This class primary responsibility is handling creating/deleting the
    ansible inventory for the carbon ansible action.
    """

    def __init__(self, hosts, all_hosts, data_dir, results_dir, static_inv_dir=None):
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
        self.lock_file = '/tmp/cbn_%s.lock' % os.path.basename(data_dir)

        # set & create the inventory directory
        if static_inv_dir:
            if 'inventory' in (os.path.basename(static_inv_dir),
                               os.path.basename(os.path.dirname(static_inv_dir))):
                self.inv_dir = os.path.expandvars(
                    os.path.expanduser(static_inv_dir)
                )
            else:
                self.inv_dir = os.path.expandvars(
                    os.path.expanduser(os.path.join(static_inv_dir, 'inventory'))
                )
            if not os.path.isdir(self.inv_dir):
                os.makedirs(self.inv_dir)
        else:
            self.inv_dir = os.path.join(results_dir,
                                        'inventory')
            if not os.path.isdir(self.inv_dir):
                os.makedirs(self.inv_dir)

        # set the master inventory
        self.master_inv = os.path.join(self.inv_dir, 'master-%s' % os.path.basename(data_dir))

        # set the unique inventory
        self.unique_inv = os.path.join(self.inv_dir, 'unique-%s' % uuid4())

        # defines the custom group to run the play against
        self.group = 'hosts'

    def create_master(self):
        """Create the master ansible inventory.

        This method will create a master inventory which contains all the
        hosts in the given scenario. Each host will have a group/group:vars.
        """
        try:
            # create parser object, raw config parser allows keys with no values
            config = RawConfigParser(allow_no_value=True)
            # disable default behavior to set values to lower case
            config.optionxform = str

            # get the lock
            self.acquire()

            # check for any old master inventories and delete them.
            # This is specifically for those using the static
            # inventory feature
            if glob(os.path.join(self.inv_dir, 'master*')):
                for f in glob(os.path.join(self.inv_dir, 'master*')):
                    if f != self.master_inv:
                        os.remove(f)

            # do not create master inventory if already exists
            # load it and keep building upon it
            if os.path.exists(self.master_inv):
                with open(self.master_inv) as f:
                    config.readfp(f)

            for host in self.all_hosts:
                section = host.name
                section_vars = '%s:vars' % section

                if hasattr(host, 'role') or hasattr(host, 'groups'):
                    for attr in ['role', 'groups']:
                        for sect in getattr(host, attr, []):
                            host_section = sect + ":children"
                            if host_section in config.sections():
                                config.set(host_section, host.name)
                            else:
                                config.add_section(host_section)
                                config.set(host_section, host.name)

                    # create section(s)
                    for item in [section, section_vars]:
                        config.add_section(item)

                    # add ip address to group
                    if isinstance(host.ip_address, dict):
                        config.set(section, host.ip_address.get('public'))
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

            # release the lock
            self.release()
        except Exception as ex:
            self.release()
            raise ex

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
            if hasattr(host, 'role') or hasattr(host, 'groups'):
                config.add_section(host.name)

        # add specific hosts to the group to run the action against
        for host in self.hosts:
            config.set(main_section, host.name)

        # check for any old/stale unique inventories and delete them.
        # This is incase unique inventories from previous runs were left
        # Stale unique inventories can cause issues while creating new unique ones
        if glob(os.path.join(self.inv_dir, 'unique*')):
            for f in glob(os.path.join(self.inv_dir, 'unique*')):
                self.logger.debug("Found stale unique inv %s. Deleting this file" % f)
                os.remove(f)

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
        cfg_str = ''
        new_section = False
        for section in parser.sections():
            if new_section:
                cfg_str += '\n'
            cfg_str += '[' + section.strip() + ']' + '\n'
            new_section = False
            for k, v in parser.items(section):
                if v:
                    cfg_str += k + '=' + v
                else:
                    cfg_str += k
                cfg_str += '\n'
            new_section = True
        self.logger.debug('\n' + cfg_str)
