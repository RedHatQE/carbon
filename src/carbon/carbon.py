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
    carbon.scenario

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os
import sys
import collections
from threading import Lock
import yaml
import taskrunner

from . import __name__ as __carbon_name__
from .config import Config, ConfigAttribute
from .constants import TASKLIST
from .core import CarbonException, LoggerMixin
from .helpers import LockedCachedProperty, get_root_path
from .resources import Scenario, Host, Action, Report, Execute
from .tasks import ValidateTask, ProvisionTask
from .tasks import OrchestrateTask, ExecuteTask
from .tasks import ReportTask, CleanupTask


# a lock used for logger initialization
_logger_lock = Lock()

# A pipeline is a tuple with a name, type and a list of tasks.
# The Carbon object will have a list of pipelines that holds
# all types of pipelines and a list of tasks associated with the
# type of the pipeline.
Pipeline = collections.namedtuple('Pipeline', ('name', 'type', 'tasks'))


class Carbon(LoggerMixin):
    """
    The Carbon object acts as the central object. We call this object
    'the carbon compound'. Like in chemistry, a carbon molecule helps on the
    construction of compounds of other molecules. We can use this analogy
    to understand how Carbon object creates compounds of 'resources'.

    The valid resources for Carbon can be found at ~carbon.resources package.
    These resources have special connection with carbon, which allows carbon
    to run the resources tasks, without the need to understand each resource
    in depth. Think of all caron resources as instances that are blessed by
    Carbon object. A carbon compound can have as many resource as it can.

    Once a compound of resources is defined, the function ~self.run will
    take care of running all the tasks needed to have the compound of
    resources up and running.

    The Carbon object passes through 6 main stages:
    (see all types of tasks at ~carbon.tasks package)

    1. Validation - a pipeline of tasks instances of ValidationTask.
    2. Provision - a pipeline of tasks instances of ProvisionTask.
    3. Orchestrate - a pipeline of tasks instances of OrchestrateTask.
    4. Execute - a pipeline of tasks instances of ExecuteTask.
    5. Report - a pipeline of tasks instances of ReportTask.
    6. Cleanup - a pipeline of tasks instances of CleanupTask.

    Each resource can have its own set of tasks. Theses tasks will be
    loaded within the central pipeline, the ~self.pipelines object.

    """

    # The class that is used for the ``config`` attribute of this app.
    # Defaults to :class:`~carbon.Config`.
    #
    # Example use cases for a custom class:
    #
    # 1. Default values for certain config options.
    # 2. Access to config values through attributes in addition to keys.
    config_class = Config

    # The debug flag.  Set this to ``True`` to enable debugging of the
    # application.  In debug mode the debugger will kick in when an unhandled
    # exception occurs and the integrated server will automatically reload
    # the application if changes in the code are detected.
    #
    # This attribute can also be configured from the config with the ``DEBUG``
    # configuration key.  Defaults to ``False``.
    debug = ConfigAttribute('DEBUG')

    # The name of the logger to use.  By default the logger name is the
    # package name passed to the constructor.
    logger_name = ConfigAttribute('LOGGER_NAME')

    # The log level. Set this to your log level of choice to display less or
    # more log messages.
    #
    # This attribute can also be configured by carbon run --log-level info or
    # from the config with the ``LOG_LEVEL`` configuration key. Defaults to
    # ``info``.
    log_level = ConfigAttribute('LOG_LEVEL')

    # If a secret key is set, cryptographic components can use this to
    # sign messages and other things.
    secret_key = ConfigAttribute('SECRET_KEY')

    # The pipeline of pipelines. All pipelines in the lists starts an
    # empty tasks list and tasks will be added later when the
    # :function:`~carbon.Carbon.run` is executed. The framework will run
    # through each resource object within the scenario and look for
    # variables that start with `_task_`. If found, it will verify what
    # type of task it is and add into its respective task_list.
    _pipelines = [
        Pipeline('validate', ValidateTask, list()),
        Pipeline('provision', ProvisionTask, list()),
        Pipeline('orchestrate', OrchestrateTask, list()),
        Pipeline('execute', ExecuteTask, list()),
        Pipeline('report', ReportTask, list()),
        Pipeline('cleanup', CleanupTask, list()),
    ]

    # Default configuration parameters.
    default_config = {
        'DEBUG': False,
        'LOGGER_NAME': __carbon_name__,
        'LOG_LEVEL': 'info',
        'SECRET_KEY': 'secret-key',
    }

    def __init__(self, import_name, root_path=None, log_level=None):

        # The name of the package or module.  Do not change this once
        # it was set by the constructor.
        self.import_name = import_name

        if root_path is None:
            root_path = get_root_path(self.import_name)

        # Where is the app root located? Calling the client will
        # always be the place where carbon is installed (site-packages)
        self.root_path = root_path

        self.config = self.make_config()

        if log_level:
            self.log_level = log_level

        # Load/process carbon configuration settings in the following order:
        #    /etc/carbon/carbon.cfg
        #    ./carbon.cfg (location where carbon is run)
        #    export CARBON_SETTINGS = {} (environment variable)
        self.config.from_pyfile('/etc/carbon/carbon.cfg', silent=True)
        self.config.from_pyfile(os.path.join(os.getcwd(), 'carbon.cfg'),
                                silent=True)
        self.config.from_envvar('CARBON_SETTINGS', silent=True)

        # Setup logging handlers
        self.create_carbon_logger(name=self.config['LOGGER_NAME'],
                                  log_level=self.config['LOG_LEVEL'])
        self.create_taskrunner_logger(log_level=self.config['LOG_LEVEL'])

        self.scenario = Scenario()
        self.creds = {}

    @LockedCachedProperty
    def name(self):
        """The name of the application.  This is usually the import name
        with the difference that it's guessed from the run file if the
        import name is main.  This name is used as a display name when
        Carbon needs the name of the scenario.  It can be set and overridden
        to change the value.
        """
        if self.import_name == '__main__':
            fn = getattr(sys.modules['__main__'], '__file__', None)
            if fn is None:
                return '__main__'
            return os.path.splitext(os.path.basename(fn))[0]
        return self.import_name

    def make_config(self):
        """
        Used to create the config attribute by the Carbon constructor.

        :copyright: (c) 2015 by Armin Ronacher.
        """
        root_path = self.root_path
        return self.config_class(root_path, self.default_config)

    def load_from_yaml(self, filepath):
        """
        Given the YAML filename with the scenario description, this
        function will load all resources described in the file with
        the carbon object.

        The main sections of the YAML descriptor (provision, orchestrate,
        execute and report) will be taken of the data in its respective
        data object. All the rest of the attributes within the YAML file
        will be loaded into the ~self.scenario object. The additional
        attributes within the file will be ignored by the Scenario
        resource.

        Once each data section is taken of the main descriptor, it will
        then be be loaded in each respective lists within the
        ~self.scenario object.

        :param filepath: the full path for the YAML file descriptor
        :return:
        """
        data = dict(yaml.safe_load(open(filepath, 'r')))

        try:
            cred_items = data.pop('credentials', None)
            pro_items = data.pop('provision', None)
            orc_items = data.pop('orchestrate', None)
            exe_items = data.pop('execute', None)
            rpt_items = data.pop('report', None)
        except KeyError as ex:
            raise CarbonException(ex)

        data["filename"] = filepath
        self.scenario.load(data)

        # Set scenario id
        self.scenario.set_scenario_id()

        self._load_credentials(cred_items)

        self._load_resources(Host, pro_items)
        self._load_resources(Action, orc_items)
        self._load_resources(Execute, exe_items)
        self._load_resources(Report, rpt_items)

        # Each resource has to be an instance of its own type.
        # This loop goes through the list of hosts, then for each
        # host it goes through the list of packages. Each instance
        # of package is added back into a Host object, loaded as a
        # Package object.
        # for hst in self._extract_hosts(data):
        #     host = Host(hst)
        #     for pkg in self._extract_packages(hst):
        #         host.packages.append(Action(pkg))
        #     self.scenario.add_hosts(host)

    def _load_credentials(self, creds_list):
        """Load all provider credentials for the scenario.

        It will construct a dictionary containing entries for each credential
        defined in the YAML.

        :param creds_list: A list of provider credentials
        :return: None
        """
        for item in creds_list:
            try:
                _name = item.pop('name')
                self.creds[_name] = item
            except KeyError as ex:
                raise CarbonException(ex)

    def _load_resources(self, res_type, res_list):
        """
        Load the resource in the scenario list of `res_type`.

        The scenario holds a list of each resource type: hosts, actions,
        reports, etc. This function takes what type of resource is in
        list it calls ~self.scenario.add_resource for each item in the
        list of the given resources.

        For example, if we call _load_resources(Host, hosts_list), the
        function will go through each item in the list, create the
        resource with Host(parameter=item) and load it within the list
        ~self.hosts.

        :param res_type: The type of resources the function will load into its list
        :param res_list: A list of resources dict
        :return: None
        """
        # No resources defined, then exit
        if not res_list:
            return

        for item in res_list:
            if res_type == Host:
                # Set all available provider credentials into host object
                item['provider_creds'] = self.creds
            self.scenario.add_resource(res_type(
                parameters=item, scenario_id=self.scenario.scenario_id))

    def _add_task_into_pipeline(self, t):
        """
        Given a task object, it will find in which pipeline within
        ~self.pipelines it belongs to and add it into its respective
        queue of tasks.

        :param t: a task object instance from one of the carbon.tasks package
        """
        for pipeline in self._pipelines:
            if pipeline.type.__name__ == t['task'].__name__:
                pipeline.tasks.append(t)

    def run(self, tasklist=TASKLIST):
        """
        This function assumes there are zero or more tasks to be
        loaded within the list of pipelines: ~self.pipelines.

        It will run through all resources within the ~self.scenario
        object (lists of hosts, actions, executes, reports), including
        tasks associated with the ~self.scenario itself, and find if any
        of them has a task to be loaded in the pipelines.

        Once a task is found, it is loaded within its respective
        pipeline and then each pipeline is sent to taskrunner execution.
        For every pipeline within ~self.pipelines,
        """

        # check if scenario was set
        if self.scenario is None:
            raise Exception(
                "You must set a scenario before run the framework.")

        # get the list of resources for each main section, including
        # the ~self.scenario object itself.
        for host in self.scenario.hosts:
            for host_task in host.get_tasks():
                self._add_task_into_pipeline(host_task)

        for action in self.scenario.actions:
            for action_task in action.get_tasks():
                self._add_task_into_pipeline(action_task)

        for execute in self.scenario.executes:
            for execute_task in execute.get_tasks():
                self._add_task_into_pipeline(execute_task)

        for report in self.scenario.reports:
            for report_task in report.get_tasks():
                self._add_task_into_pipeline(report_task)

        for scenario_task in self.scenario.get_tasks():
            self._add_task_into_pipeline(scenario_task)

        try:
            for pipeline in self._pipelines:
                if pipeline.name in tasklist:
                    pass
                else:
                    continue

                self.logger.info("." * 50)
                self.logger.info("=> Starting tasks on pipeline: %s",
                                 pipeline.name)
                if not pipeline.tasks:
                    self.logger.warn("   ... nothing to be executed here ...")
                else:
                    taskrunner.execute(pipeline.tasks, cleanup='always')
                self.logger.info("." * 50)
        except taskrunner.TaskExecutionException as ex:
            self.logger.error(ex)
