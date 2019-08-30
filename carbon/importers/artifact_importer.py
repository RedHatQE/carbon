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

from ..core import CarbonImporter
from ..exceptions import CarbonImporterError
from ..helpers import find_artifacts_on_disk, search_artifact_location_dict, DataInjector


class ArtifactImporter(CarbonImporter):

    __importer_name__ = 'artifact-importer'

    def __init__(self, report):

        super(ArtifactImporter, self).__init__(report)

        self.artifact_paths = []

        # use the profile dict as a request object to the plugin
        report_profile = self.report.profile()
        report_profile.update(dict(data_folder=self.data_folder, workspace=self.workspace,
                                   provider_credentials=self.provider_credentials,
                                   artifacts=[]))

        # build the config params that might be useful to plugin implementation
        plugin_name = getattr(self.report, 'importer_plugin').__plugin_name__
        config_params = dict()
        for k, v in self.config.items():
            if plugin_name.upper() in k:
                config_params[k.lower()] = v

        report_profile.update(dict(config_params=config_params))

        # check if user specified data pass-through injection
        for execute in self.report.executes:
            injector = DataInjector(execute.all_hosts)
            report_name = injector.inject(self.report.name)
            report_profile['name'] = report_name

        # setup plugin with profile dict
        self.plugin = getattr(self.report, 'importer_plugin')(report_profile)

    def validate_artifacts(self):

        # check that the execute object collected artifacts
        art_paths = []
        '''for execute in self.report.executes:
            if execute.artifact_locations:
                art_paths = search_artifact_location_dict(art_locations=execute.artifact_locations,
                                                          report_name=self.plugin.profile['name'])
            else:
                self.logger.warning('The specified execute, %s, does not have any artifacts '
                                 'with it.' % execute.name)

        # check that the list generated searching the dictionary is not empty
        if not art_paths:
            self.logger.warning('Could not find %s as one of the artifacts that was collected. Checking the '
                             'data directories anyways.'
                                      % self.report.name)
            self.artifact_paths = find_artifacts_on_disk(data_folder=self.data_folder,
                                                         path_list=[self.plugin.profile['name']],
                                                         art_location_found=False)
        else:
            self.artifact_paths = find_artifacts_on_disk(data_folder=self.data_folder, path_list=art_paths)'''
        for execute in getattr(self.report, 'executes'):
            if not execute.artifact_locations:
                self.logger.warning('The specified execute, %s, does not have any artifacts '
                                    'with it.' % execute.name)
                self.artifact_paths.extend(find_artifacts_on_disk(data_folder=self.data_folder,
                                                                  report_name=self.plugin.profile['name']))
            else:
                self.artifact_paths.extend(find_artifacts_on_disk(data_folder=self.data_folder,
                                                                  report_name=self.plugin.profile['name'],
                                                                  art_location=execute.artifact_locations))
        if not self.artifact_paths:
            raise CarbonImporterError('No artifact could be found on the Carbon controller data folder.')

    def import_artifacts(self):
        self.validate_artifacts()
        self.plugin.artifacts = self.artifact_paths
        try:
            results = self.plugin.import_artifacts()
            setattr(self.report, 'import_results', results)
        except Exception as ex:
            self.logger.error(ex)
            setattr(self.report, 'import_results', getattr(self.plugin, 'import_results'))
            raise CarbonImporterError('Failed to import artifact %s' % self.report.name)
