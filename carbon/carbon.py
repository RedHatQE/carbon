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
    carbon

    Carbon a framework to test product interoperability.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import errno
import shutil
import sys
import tempfile
from threading import Lock

import blaster
import os
import yaml
from flask.config import Config, ConfigAttribute
from flask.helpers import locked_cached_property, get_root_path

from . import __name__ as __carbon_name__
from .constants import TASKLIST, STATUS_FILE, RESULTS_FILE
from .core import CarbonError, LoggerMixin, PipelineBuilder, TimeMixin
from .helpers import file_mgmt, gen_random_str
from .resources import Scenario, Host, Action, Report, Execute

# a lock used for logger initialization
_logger_lock = Lock()


class ResultsMixin(object):
    """Carbons results mixin class.

    This class provides an easy interface for processing results from task
    executions per resources.
    """
    _results = dict(tasks=[],
                    last_executed=None,
                    last_executed_status=None,
                    executed_tasks=None)

    _task_results = dict()

    @property
    def results(self):
        """Return the results for the scenario."""
        return self._results

    @results.setter
    def results(self, value):
        """Raise exception when setting scenario results directly."""
        raise ValueError('You cannot set scenario results directly.')

    def update_results(self, task_name, status, blaster_data):
        """Update scenario results.

        :param task_name: Name of executed task.
        :param status: Status of executed task.
        :param blaster_data: Data returned by blaster.
        """
        self._results['last_executed'] = task_name
        self._results['last_executed_status'] = status

        if task_name not in self._task_results:
            self._task_results[task_name] = dict(resources=[])

        self._task_results[task_name]['status'] = status

        for item in blaster_data:
            if 'resource' in item:
                _res = item['resource']
            elif 'host' in item:
                _res = item['host']
            elif 'package' in item:
                _res = item['package']
                setattr(_res, 'methods', item['methods'])

            self._task_results[task_name]['resources'].append(
                {
                    _res.__class__.__name__.lower(): {
                        'name': _res.name,
                        'methods_executed': item['methods']
                    }
                }
            )

        self._results['executed_tasks'] = self._task_results

    @property
    def tasks(self):
        """Return the tasks to run for the scenario."""
        return self._results['tasks']

    @tasks.setter
    def tasks(self, value):
        """Set the tasks to run for the scenario.

        :param value: List of tasks to run.
        """
        self._results['tasks'] = value

    def read_status_file(self, status_file):
        """Read an existing scenario status file.

        :param status_file: Absolute path to the status file.
        """
        if os.path.isfile(status_file):
            self._results = file_mgmt('r', status_file)

    def write_status_file(self, status_file):
        """Write a scenario status file.

        :param status_file: Absolute path for the status file.
        """
        file_mgmt('w', status_file, self.results)


class Carbon(LoggerMixin, ResultsMixin, TimeMixin):
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

    # set a workspace folder, for where files will be updated
    data_folder = ConfigAttribute('DATA_FOLDER')

    # Default configuration parameters.
    default_config = {
        'DATA_FOLDER': tempfile.gettempdir(),
        'LOGGER_NAME': __carbon_name__,
        'LOG_LEVEL': 'info',
    }

    def __init__(self, import_name, root_path=None, log_level=None,
                 data_folder=None, assets_path=None):

        # The name of the package or module.  Do not change this once
        # it was set by the constructor.
        self.import_name = import_name

        self._uid = gen_random_str(10)

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

        # Set custom data folder, if data_folder is pass as parameter to Carbon
        if data_folder:
            self.config['DATA_FOLDER'] = data_folder

        # define the results folder
        self.config['RESULTS_FOLDER'] = os.path.join(
            self.config['DATA_FOLDER'], '.results')

        # Generate the UID for the carbon life-cycle based on data_folder
        self.config['DATA_FOLDER'] = os.path.join(self.config['DATA_FOLDER'],
                                                  self.uid)

        # Why a results folder and a data folder? The data folder is a unique
        # folder that is created for each carbon execution. This folder will
        # contain files generated by carbon for that specific execution. What
        # if you want to run a certain task, then run another task all using
        # a results file stored in a previous carbon data folder? Well its hard
        # to determine the data folder since its a random unique folder name.
        # The results folder will save the last executed carbon task. This way
        # you can point your next carbon task to run the scenario file from
        # this given folder.
        # i.e.
        #   provision task and then want to run orchestrate separately
        #       - carbon run -s scenario.yml -t provision
        #       - carbon run -s /tmp/.results/results.yml -t orchestrate

        try:
            os.makedirs(self.config['DATA_FOLDER'])
        except IOError as ex:
            if ex.errno == errno.EACCES:
                raise CarbonError("You don't have permission to create '"
                                  "the data folder.")
            else:
                raise CarbonError('Error creating data folder - '
                                  '{0}'.format(ex.message))

        # create the results folder
        try:
            os.makedirs(self.config['RESULTS_FOLDER'])
        except OSError:
            # results folder exists, its okay to continue since we overwrite
            # this folder's files after each execution
            pass
        except IOError as ex:
            if ex.errno == errno.EACCES:
                raise CarbonError("You don't have permission to create '"
                                  "the results folder.")
            else:
                raise CarbonError('Error creating results folder - '
                                  '{0}'.format(ex.message))

        # configure loggers
        self.create_logger(__carbon_name__, self.config)
        self.create_logger('blaster', self.config)
        # pykwalify logging disabled for too much logging
        # self.create_logger('pykwalify.core', self.config)

        # the assets can be located wherever the user wants or it
        # will look at the running folder (getcwd())
        if assets_path:
            self.assets_path = assets_path
        else:
            self.assets_path = os.getcwd()
            self.logger.warn('Assets path were not set, thefore the'
                             ' framework setting for the running directory.'
                             ' You may have problems if your scenario needs'
                             ' to use assets such file, keys, etc.')
        self.config['ASSETS_PATH'] = self.assets_path

        self.scenario = Scenario(config=self.config)

    @locked_cached_property
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

    @locked_cached_property
    def uid(self):
        return self._uid

    @locked_cached_property
    def data_folder(self):
        return self.config['DATA_FOLDER']

    @locked_cached_property
    def status_file(self):
        return os.path.join(self.data_folder, STATUS_FILE)

    @locked_cached_property
    def results_file(self):
        return os.path.join(self.data_folder, RESULTS_FILE)

    def make_config(self):
        """
        Used to create the config attribute by the Carbon constructor.

        :copyright: (c) 2015 by Armin Ronacher.
        """
        root_path = self.root_path
        return self.config_class(root_path, self.default_config)

    def load_from_yaml(self, filedata):
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

        :param filedata: the full data object for the YAML file descriptor
        :return:
        """

        self.scenario.yaml_data = filedata
        data = dict(yaml.safe_load(filedata))

        try:
            cred_items = data.pop('credentials', None)
            pro_items = data.pop('provision', None)
            orc_items = data.pop('orchestrate', None)
            exe_items = data.pop('execute', None)
            rpt_items = data.pop('report', None)
        except KeyError as ex:
            raise CarbonError(ex)

        self.scenario.load(data)

        # setting up credentials
        if "CREDENTIALS" in self.config and self.config["CREDENTIALS"]:
            for item in self.config["CREDENTIALS"]:
                self.scenario.add_credentials(item)
        if cred_items:
            for item in cred_items:
                self.scenario.add_credentials(item)
        if not self.scenario.credentials:
            raise CarbonError("Credentials are not being set!!")

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

        :param res_type: The type of resources the function will load into its
            list
        :param res_list: A list of resources dict
        :return: None
        """
        # No resources defined, then exit
        if not res_list:
            return

        for item in res_list:
            if res_type == Host and item['provider'] != 'static':
                # Set all available provider credentials into host object
                item['provider_creds'] = self.scenario.credentials
            self.scenario.add_resource(
                res_type(config=self.config,
                         parameters=item))

    def _copy_assets(self):
        """
        Copy the assets from the `self.assets_path` to the assets
        folder within the `self.data_folder`.
        """
        local_assets_folder = os.path.join(self.data_folder, 'assets')

        # create assets folder
        try:
            os.makedirs(local_assets_folder)
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                pass
            else:
                raise CarbonError('Error creating assets folder - %s' %
                                  ex.message)

        for asset in self.scenario.get_assets_list():
            src_file = os.path.join(self.assets_path, asset)
            dst_file = os.path.join(local_assets_folder, asset)

            # if asset is declared within a folder, the destination
            # parent folder needs to be created to avoid `errno.ENOENT`.
            dst_folder = os.path.dirname(dst_file)
            if not os.path.isdir(dst_folder):
                os.makedirs(dst_folder)
            del dst_folder

            if os.path.isdir(src_file):
                shutil.copytree(src=src_file, dst=dst_file)
            else:
                shutil.copy2(src=src_file, dst=dst_file)

    def run(self, tasklist=TASKLIST):
        """
        This function assumes there are zero or more tasks to be
        loaded within the list of pipelines: ~self.pipelines.

        It will run through all resources within the ~self.scenario
        object (lists of hosts, actions, executes, reports), including
        tasks associated with the ~self.scenario itself, and find if any
        of them has a task to be loaded in the pipelines.

        Once a task is found, it is loaded within its respective
        pipeline and then each pipeline is sent to blaster blastoff.
        For every pipeline within ~self.pipelines,
        """
        self.tasks = tasklist

        # check if scenario was set
        if self.scenario is None:
            raise CarbonError(
                'You must set a scenario before running the framework!'
            )

        # check that all assets are copied to assets folder (if assets exist)
        try:
            self._copy_assets()
        except shutil.Error as ex:
            self.logger.error('Error while copying assets. %s' % ex.message)
            raise CarbonError('Error while copying assets %s' % ex.message)
        except IOError as ex:
            if ex.errno == errno.ENOENT:
                self.logger.error(
                    'Error while copying the asset "%s"' % ex.filename
                )
                raise CarbonError('Asset "%s" does not exist. Check if '
                                  'the asset folder was set correctly.' %
                                  ex.filename)
            else:
                raise CarbonError(
                    'Error while copying assets. Msg: %s' % ex.message
                )

        try:
            # save start time
            self.start()

            # overall status
            status = 0

            for task in self.tasks:

                # create a pipeline builder object
                pipe_builder = PipelineBuilder(task)

                # check if carbon supports the task
                if not pipe_builder.is_task_valid():
                    self.logger.warn('Task %s is not valid by carbon.', task)
                    continue

                # build task pipeline
                pipeline = pipe_builder.build(self.scenario)

                self.logger.info('.' * 50)
                self.logger.info('Starting tasks on pipeline: %s',
                                 pipeline.name)

                # check if pipeline has tasks to be run
                if not pipeline.tasks:
                    self.logger.warn('... no tasks to be executed ...')
                    continue

                # create blaster object with pipeline to run
                blast = blaster.Blaster(pipeline.tasks)

                # blast off the pipeline list of tasks
                data = blast.blastoff(
                    serial=not pipeline.type.__concurrent__,
                    raise_on_failure=True
                )

                # update results
                self.update_results(pipeline.name, status, data)

                # reload resource objects
                self.scenario.reload_resources(data)

                self.logger.info("." * 50)
        except blaster.BlasterError as ex:
            # set overall status
            status = 1

            self.logger.error(ex)

            # update results
            self.update_results(pipeline.name, status, ex.results)

            # reload resource objects
            self.scenario.reload_resources(ex.results)
        finally:
            # save end time
            self.end()

            self.logger.info('Carbon run time duration: %dh:%dm:%ds' %
                             (self.hours, self.minutes, self.seconds))

            # write carbon status file
            self.write_status_file(self.status_file)
            shutil.copy(self.status_file, self.config['RESULTS_FOLDER'])
            self.logger.info('Scenario status file ~ %s' % self.status_file)

            file_mgmt('w', self.results_file, self.scenario.profile())
            shutil.copy(self.results_file, self.config['RESULTS_FOLDER'])
            self.logger.info('Scenario results file ~ %s' % self.results_file)

            # Raise final carbon exception based on status of task execution
            if status:
                raise CarbonError(
                    'Scenario %s failed to run successfully!' %
                    self.scenario.name
                )
