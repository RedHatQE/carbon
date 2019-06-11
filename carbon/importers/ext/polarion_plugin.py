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
from ...exceptions import PolarionImporterError
from polar.polar import Polar, PolarError
import json


class PolarionImporterPlugin(ImporterPlugin):

    __plugin_name__ = 'polarion'

    def __int__(self, profile):

        super(PolarionImporterPlugin, self).__init__(profile)

    def import_artifacts(self):
        results = []
        csv_file = self._check_csv_file(self.provider_params)
        polarion_props = self._translate_test_params(self.provider_params)
        config_params = self._parse_config_params(self.config_params)
        polarion = Polar(credentials=self.provider_credentials,
                         polar_params=config_params)

        try:
            self.logger.info('Attempting to import xUnit file.')
            if polarion_props is not None:
                self.logger.debug('About to do conversion.')
                results = polarion.convert_xunit(xunit_files=self.artifacts,
                                                 polarion_props=polarion_props,
                                                 csv_file=csv_file)
            else:
                # If no polarion_props assume it's already been done and we just
                # need to get the file data and import it.
                data = ''
                for artifact in self.artifacts:
                    with open(artifact, 'r') as f:
                        data = f.read()
                    results.append((artifact, data))
                    data = ''

            job_ids = polarion.import_xunit(results)

            return self._parse_import_results(polarion.listen_for_import(job_ids))
        except (PolarError) as ex:
            self.import_results = self._parse_import_results(ex.results)
            raise
        # return polarion.import_process(self.artifacts, polarion_props)

    def aggregate_artifacts(self):
        pass

    def cleanup_artifacts(self):
        pass

    def _translate_test_params(self, params):
        json_props = None
        ts_props = dict()

        # First check if project-id has been specified since that is a min
        # requirement for polarion
        try:
            ts_props['polarion-project-id'] = params['project_id']
        except KeyError:
            self.logger.debug('Key "project_id" not specified')

        # Next check that any other testsuite properties specified
        try:
            ts_props.update(params['testsuite_properties'])
        except KeyError:
            self.logger.debug('Key "testsuite_properties" not specified')

        # Finally check if any testcase properties specified
        try:
            json_props = dict(properties=ts_props, casemap=params['testcase_properties'])
        except KeyError:
            self.logger.debug('Key "testcase_properties" not specified')
            json_props = dict(properties=ts_props)

        self.logger.debug('Polarion Providers params translated to the following %s' % json_props)
        return json_props

    def _parse_import_results(self, results):
        return [json.loads(json.dumps(r)) for r in results]

    def _parse_config_params(self, cparams):
        cp = dict(save_file=True, poll_interval=60, wait_timeout=900)
        if cparams:
            for k, v in cparams.items():
                if 'save_file' in k.lower():
                    cp['save_file'] = v
                if 'poll_interval' in k.lower():
                    cp['poll_interval'] = int(v)
                if 'wait_timeout' in k.lower():
                    cp['wait_timeout'] = int(v)

        self.logger.debug('Polarion config params translated to the following %s' % cp)
        return cp

    def _check_csv_file(self, params):

        if 'testcase_properties' in params and 'testcase_csv_file' in params:
            raise PolarionImporterError('Both testcase_properties and testcase_csv_file have been supplied. \
            Please provide one or the other.')
        elif 'testcase_csv_file' in params:
            self.logger.info('Using a csv file for testcase properties.')
            return params['testcase_csv_file']
        else:
            return None
