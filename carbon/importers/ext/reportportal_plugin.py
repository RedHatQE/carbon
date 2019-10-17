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

from ...core import ImporterPlugin
import json
import os
import re
from ..._compat import string_types
from ...helpers import exec_local_cmd
from ...exceptions import ReportPortalImporterError, CarbonReportError


class ReportPortalPlugin(ImporterPlugin):

    __plugin_name__ = 'reportportal'

    def __int__(self, profile):

        super(ReportPortalPlugin, self).__init__(profile)

    def import_artifacts(self):
        # Flag is set when Carbon creates the rp config file
        rp_file_flag = False
        if self.provider_params.get('json_path'):
            rp_config_file = self._validate_rp_json_path_exist(self.provider_params.get('json_path'))
            self._validate_rp_json(rp_config_file)
        else:
            rp_config_file = self._convert_params_to_rp_json()
            rp_file_flag = True

        payload_dir = self._create_rp_payload_dir()

        # setting up log directory:
        if not os.path.isdir(os.path.abspath(os.path.join(self.data_folder, "rp_logs"))):
            os.system('mkdir %s' % os.path.abspath(os.path.join(self.data_folder, "rp_logs")))

        # adding --debug to collect all the report portl client log which will be stored under the data folder
        # as rp_preproc.log
        cmd = 'rp_preproc -c ' + rp_config_file + ' -d ' + payload_dir + ' -l ' + self.data_folder + \
              '/rp_logs/rp_preproc.log' + ' --debug'

        results = self._execute_rp_cmd(cmd)

        # Checking for reportportal_save_file flag .
        # Checking if Carbon created the rp config file
        # Removing the Carbon created json config file if reportportal_save_file is set to False
        if rp_file_flag and self.config_params.get("reportportal_save_json_config", 'False').lower() == 'false':
            self.logger.info("Deleting file %s" % rp_config_file)
            os.remove(rp_config_file)

        return results

    def _execute_rp_cmd(self, cmd):

        """This method is used to execute the rp-preproc command using the exe_local_xmd method in helpers.py
        :param cmd: rp_preproc command
        :return: a list of results frpm report-portal
        :rtype: list
        """
        # try:
        results = dict()
        self.logger.info("Executing command %s" % cmd)
        self.logger.info("Please wait for the report portal command to complete")
        rc, op0, op1 = exec_local_cmd(cmd)
        self.logger.info("Report portal command completed")
        if rc == 0:
            json_op0 = json.loads(op0)
            results['status'] = 'passed'
            if json_op0['reportportal'].get('auto_dashboard'):
                results['dashboard_url'] = json_op0['reportportal'].get('auto_dashboard').get('url')
            if json_op0['reportportal'].get('merged_launch'):
                results['merged_launch_id'] = json_op0['reportportal'].get('merged_launch')
            else:
                results['launch_ids'] = json_op0['reportportal'].get('launches')
            self.logger.info("Import to Report Portal completed successfully")
        else:
            raise ReportPortalImporterError("There was an error running the report portal command %s %s %s"
                                            % (rc, op0, op1))
        return results

    def _create_rp_payload_dir(self):
        """
        This method looks at the collected artifacts/artifact paths and determines if the artifacts are in correct dir
        structure required for the rp client payload. If the structure is correct then it passes the dir given in the
        artifacts path as the payload dir. If the structure is not correct , new payload dir structure is created as
        rp_payload/results under datafolder and all xml files are copied in the rp_payload/results folder.
        This becomes the payload dir for the rp client .

        :return: payload dir
        :rtype: str
        """

        # TODO this logic does not work when the self.artifacts have structured and unstructured files
        # TODO this needs to be modified

        res_flag = False
        for art in self.artifacts:
            # Checking if the path consists of a results folder
            if re.match(r"^results$", os.path.basename(art)):
                dir = os.path.dirname(art)
                res_flag = True
                break
            elif re.match(r"^results$", art.split('/')[-2]):
                dir = os.path.dirname(os.path.dirname(art))
                res_flag = True
                break

        if res_flag:
            self.logger.info("results dir is present in artifacts.Assuming payload structure to be correct.")
            self.logger.info("This dir %s will be used as the report portal payload" % dir)
            return dir
        else:
            self.logger.info("results dir is not present in artifacts. The payload structure needs a results dir.")
            self.logger.info("Creating results dir and copying only xml files.All other files will be ignored")

            payload_rel_path = (os.path.join(self.data_folder, 'rp_payload'))
            # creating a rp_payload dir under data folder
            if not os.path.isdir(os.path.abspath(payload_rel_path)):
                os.system('mkdir %s' % os.path.abspath(payload_rel_path))
            # creating a results folder under the rp_payload dir
            os.system('mkdir %s' % os.path.abspath(os.path.join(payload_rel_path, 'results')))

            for p in self.artifacts:
                if '.xml' in p:
                    os.system('cp  "%s" "%s"' % (os.path.abspath(p),
                                                 os.path.abspath(os.path.join(payload_rel_path, 'results'))))

            return os.path.abspath(payload_rel_path)

    def _convert_params_to_rp_json(self):
        """
        This method uses the report portal provider params to create a json config file to pass it
        to the report portal client
        :return: report portal config json file
        """
        path = self.profile['workspace']
        # converting tags into a list in case they are given as strings
        if isinstance(self.provider_params.get('tags'), string_types):
            self.provider_params['tags'] = self.provider_params.get('tags').replace(' ', '').split(',')
        data = dict()

        # check for service_url is false and change it to a Boolean:
        if self.profile['provider_credentials'].get('service_url').lower() == 'false':
            sev_url = False
        else:
            sev_url = self.profile['provider_credentials'].get('service_url', False)

        data['rp_preproc'] = {
                               "service_url": sev_url,
                               "payload_dir": ""
                            }
        data['reportportal'] = dict()
        data['reportportal']['host_url'] = self.profile['provider_credentials'].get('rp_url')
        data['reportportal']['api_token'] = self.profile['provider_credentials'].get('api_token')
        data['reportportal']['project'] = self.provider_params.get('rp_project', "")
        data['reportportal']['merge_launches'] = self.provider_params.get('merge_launches', True)
        data['reportportal']['auto_dashboard'] = self.provider_params.get('auto_dashboard', True)
        data['reportportal']['simple_xml'] = self.provider_params.get('simple_xml', False)
        data['reportportal']['launch'] = dict()
        data['reportportal']['launch'] = {
                                          "name": self.provider_params.get('launch_name', ""),
                                          "description": self.provider_params.get('launch_description', ""),
                                          "tags": self.provider_params.get('tags', "")
                                         }

        with open(os.path.join(path, 'rp_config_file.json'), 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self._validate_rp_json(os.path.join(path, 'rp_config_file.json'))

        return os.path.join(path, 'rp_config_file.json')

    def _validate_rp_json_path_exist(self, json_path):
        """
        This method validates if the given json path is correct and the json file exist in the workspace
        :param json_path:
        :return: json file path joined with the workspace
        :rtype: str
        """
        if os.path.isfile(os.path.join(self.profile.get('workspace'), json_path)):
            return os.path.join(self.profile.get('workspace'), json_path)
        else:
            self.logger.error("Report Portal Config json file not found")
            raise CarbonReportError("Report Portal Config json file not found")

    def _validate_rp_json(self, json_file):
        """
        This method validates the given json file is in the correct json format and the keys host_url, api_token,
        project, launch name and service_url are present in the json file
        :param json_file: json file to be validated
        """
        with open(json_file) as f:
            try:
                my_json = json.load(f)
                self.logger.debug("This is the json output from the json file %s" % my_json)
            except ValueError as e:
                raise CarbonReportError("Error with json %s" % e)

            for k in ['host_url', 'api_token', 'project']:
                if not my_json['reportportal'].get(k) or not my_json['reportportal'].get(k):
                    raise CarbonReportError("The %s value in the rp config file cannot be empty" % k)
            if not my_json['reportportal']['launch'].get('name'):
                raise CarbonReportError("The %s value in the rp config file cannot be empty" % k)

    def aggregate_artifacts(self):
        raise NotImplementedError
        # code to validate the resources are present and code to zip it if necessary?

    def cleanup_artifacts(self):
        raise NotImplementedError
