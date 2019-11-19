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

import os
from ..core import CarbonImporter
from ..exceptions import CarbonImporterError
from .._compat import string_types
from ..helpers import find_artifacts_on_disk, DataInjector


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

        # check if user specified data pass-through injection
        host_list = [host for execute in self.report.executes for host in execute.all_hosts]
        if host_list:
            self.injector = DataInjector(host_list)
        else:
            # Assume no executes is assigned, so the helper
            # method fetch_executes added an attribute 'all_hosts'
            # to the report object
            self.injector = DataInjector(self.report.all_hosts)
        self.report_name = self.injector.inject(self.report.name)
        report_profile['name'] = self.report_name

        # build the config params that might be useful to plugin and instantiate
        if self.report.do_import:
            plugin_name = getattr(self.report, 'importer_plugin').__plugin_name__
            config_params = dict()
            for k, v in self.config.items():
                if plugin_name.upper() in k:
                    config_params[k.lower()] = v

            report_profile.update(dict(config_params=config_params))

            # setup plugin with profile dict
            self.plugin = getattr(self.report, 'importer_plugin')(report_profile)

    def validate_artifacts(self):

        # Check report has any executes associated. If not, proceed
        # to walk the data directory on disk.
        art_paths = []
        self.logger.debug(self.report_name)
        if getattr(self.report, 'executes'):
            for execute in getattr(self.report, 'executes'):
                # check that the execute object collected artifacts
                if not execute.artifact_locations:
                    self.logger.warning('The specified execute, %s, does not have any artifacts '
                                        'with it.' % execute.name)
                    self.artifact_paths.extend(find_artifacts_on_disk(data_folder=self.data_folder,
                                                                      report_name=self.report_name))
                else:
                    # check artifact locations for data pass-thru first
                    artifact_locations = dict()
                    for key, value in execute.artifact_locations.items():
                        dir_key = self.injector.inject(key)
                        files = [self.injector.inject(v) for v in value]
                        artifact_locations.update({dir_key: files})

                    # Perform check to walk the data directory
                    self.artifact_paths.extend(find_artifacts_on_disk(data_folder=self.data_folder,
                                                                      report_name=self.report_name,
                                                                      art_location=artifact_locations))
        else:
            self.artifact_paths.extend(find_artifacts_on_disk(data_folder=self.data_folder,
                                                              report_name=self.report_name))
        if not self.artifact_paths:
            raise CarbonImporterError('No artifact could be found on the Carbon controller data folder.')

    def import_artifacts(self):
        self.plugin.artifacts = self.artifact_paths
        try:
            results = self.plugin.import_artifacts()
            setattr(self.report, 'import_results', results)
        except Exception as ex:
            self.logger.error(ex)
            setattr(self.report, 'import_results', getattr(self.plugin, 'import_results'))
            raise CarbonImporterError('Failed to import artifact %s' % self.report.name)
