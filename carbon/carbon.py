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
import os
import sys

import blaster
import yaml

from . import __name__ as __carbon_name__
from .constants import TASKLIST, RESULTS_FILE
from .core import CarbonError, LoggerMixin, TimeMixin
from .helpers import file_mgmt, gen_random_str
from .resources import Scenario, Host, Action, Report, Execute
from .utils.config import Config
from .utils.pipeline import PipelineBuilder


class Carbon(LoggerMixin, TimeMixin):
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

    config = Config()

    def __init__(self, import_name=__carbon_name__, log_level=None,
                 data_folder=None, workspace=None):
        """Constructor.

        :param import_name: module name
        :type import_name: str
        :param log_level: logging level
        :type log_level: str
        :param data_folder: folder path for storing carbon runtime files
        :type data_folder: str
        :param workspace: scenario workspace for locating scenario files
        :type workspace: str
        """
        # The name of the package or module.  Do not change this once
        # it was set by the constructor.
        self.import_name = import_name

        self._uid = gen_random_str(10)

        # load configuration settings
        self.config.load()

        if log_level:
            self.config['LOG_LEVEL'] = log_level

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

        for f in [self.config['DATA_FOLDER'], self.config['RESULTS_FOLDER']]:
            try:
                if not os.path.exists(f):
                    os.makedirs(f)
            except (OSError, IOError) as ex:
                if ex.errno == errno.EACCES:
                    raise CarbonError("You don't have permission to create '"
                                      "the data folder.")
                else:
                    raise CarbonError('Error creating data folder - '
                                      '{0}'.format(ex))

        # configure loggers
        self.create_logger(__carbon_name__, self.config)
        self.create_logger('blaster', self.config)
        # pykwalify logging disabled for too much logging
        # self.create_logger('pykwalify.core', self.config)

        # set the workspace attribute
        if workspace:
            self.workspace = workspace
        else:
            self.workspace = os.getcwd()
            self.logger.warning(
                'Scenario workspace was not set, therefore the workspace is '
                'automatically assigned to the current working directory. You '
                'may experience problems if files needed by carbon do not '
                'exists in the scenario workspace.'
            )

        self.config['WORKSPACE'] = self.workspace

        self.scenario = Scenario(config=self.config)

    @property
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

    @property
    def uid(self):
        return self._uid

    @property
    def data_folder(self):
        return self.config['DATA_FOLDER']

    @property
    def results_file(self):
        return os.path.join(self.data_folder, RESULTS_FILE)

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

        cred_items = data.pop('credentials', None)
        pro_items = data.pop('provision', None)
        orc_items = data.pop('orchestrate', None)
        exe_items = data.pop('execute', None)
        rpt_items = data.pop('report', None)

        self.scenario.load(data)

        # setting up credentials
        if "CREDENTIALS" in self.config and self.config["CREDENTIALS"]:
            for item in self.config["CREDENTIALS"]:
                self.scenario.add_credentials(item)
                self.scenario.credentials_set_by = 'config'
        if cred_items:
            for item in cred_items:
                self.scenario.add_credentials(item)
                self.scenario.credentials_set_by = 'scenario'

        if not self.scenario.credentials:
            self.logger.warning(
                'Credentials are not set, problems may emerge in the future.'
            )

        self._load_resources(Host, pro_items)
        self._load_resources(Action, orc_items)
        self._load_resources(Execute, exe_items)
        self._load_resources(Report, rpt_items)

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
            if res_type == Host:
                # set provider credentials if applicable
                item['provider_creds'] = self.scenario.credentials
            self.scenario.add_resource(
                res_type(config=self.config,
                         parameters=item))

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
        # lists to control which tasks passed or failed
        passed_tasks = list()
        failed_tasks = list()

        # initialize overall status
        status = 0

        self.logger.info('\n')
        self.logger.info('CARBON RUN (START)'.center(79))
        self.logger.info('-' * 79)
        self.logger.info(' * Scenario    : %s' % self.scenario.name)
        self.logger.info(' * Tasks       : %s' % tasklist)
        self.logger.info(' * Data Folder : %s' % self.data_folder)
        self.logger.info(' * Workspace   : %s' % self.workspace)
        self.logger.info(' * Log Level   : %s' % self.config['LOG_LEVEL'])
        self.logger.info('-' * 79 + '\n')

        try:
            # save start time
            self.start()

            for task in tasklist:

                # create a pipeline builder object
                pipe_builder = PipelineBuilder(task)

                # check if carbon supports the task
                if not pipe_builder.is_task_valid():
                    self.logger.warning('Task %s is not valid by carbon.', task)
                    continue

                # build task pipeline
                pipeline = pipe_builder.build(self.scenario)

                self.logger.info('.' * 50)
                self.logger.info('Starting tasks on pipeline: %s',
                                 pipeline.name)

                # check if pipeline has tasks to be run
                if not pipeline.tasks:
                    self.logger.warning('... no tasks to be executed ...')
                    continue

                # create blaster object with pipeline to run
                blast = blaster.Blaster(pipeline.tasks)

                # blast off the pipeline list of tasks
                data = blast.blastoff(
                    serial=not pipeline.type.__concurrent__,
                    raise_on_failure=True
                )

                # reload resource objects
                self.scenario.reload_resources(data)

                # update list of passed tasks
                passed_tasks.append(task)

                self.logger.info("." * 50)
        except blaster.BlasterError as ex:
            # set overall status
            status = 1

            # update list of failed tasks
            failed_tasks.append(task)

            self.logger.error(ex)

            # reload resource objects
            self.scenario.reload_resources(ex.results)
        finally:
            # save end time
            self.end()

            # determine state
            state = 'FAILED' if status else 'PASSED'

            # write the updated carbon definition file
            file_mgmt('w', self.results_file, self.scenario.profile())

            # archive everything from the data folder into the results folder
            os.system('cp -r %s/* %s' % (self.data_folder, self.config[
                'RESULTS_FOLDER']))

            self.logger.info('\n')
            self.logger.info('CARBON RUN (END)'.center(79))
            self.logger.info('-' * 79)
            self.logger.info(' * Duration                   : %dh:%dm:%ds' %
                             (self.hours, self.minutes, self.seconds))
            if passed_tasks.__len__() > 0:
                self.logger.info(' * Passed Tasks               : %s' %
                                 passed_tasks)
            if failed_tasks.__len__() > 0:
                self.logger.info(' * Failed Tasks               : %s' %
                                 failed_tasks)
            self.logger.info(' * Results Folder             : %s' %
                             self.config['RESULTS_FOLDER'])
            self.logger.info(' * Latest Scenario Definition : %s' %
                             self.results_file)
            self.logger.info('-' * 79)
            self.logger.info('CARBON RUN (RESULT=%s)' % state)

            sys.exit(status)
