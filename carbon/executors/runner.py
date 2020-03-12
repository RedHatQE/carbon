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
    carbon.executor.runner

    Carbon's default and main executor.

    :copyright: (c) 2018 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import ast
import collections
import copy
import os.path
import textwrap
from ..core import CarbonExecutor
from ..exceptions import ArchiveArtifactsError, CarbonExecuteError, AnsibleServiceError
from ..helpers import DataInjector, get_ans_verbosity, is_host_localhost
from ..ansible_helpers import AnsibleService


class RunnerExecutor(CarbonExecutor):
    """ The main executor for Carbon.

    The runner class provides three different types on how you can execute
    tests. Its intention is to be generic enough where you just need to supply
    your test commands and it will process them. All tests executed against
    remote hosts will be run through ansible.
    """

    __executor_name__ = 'runner'

    _execute_types = [
        'playbook',
        'script',
        'shell'
    ]

    def __init__(self, package):
        """Constructor.

        :param package: execute resource
        :type package: object
        """
        super(RunnerExecutor, self).__init__(execute=package)

        # set required attributes
        self._name = getattr(package, 'name')
        self._desc = getattr(package, 'description')
        self._hosts = getattr(package, 'hosts')
        self.config = getattr(package, 'config')
        self.all_hosts = getattr(package, 'all_hosts')
        self.workspace = self.config['WORKSPACE']
        self.datadir = self.config['DATA_FOLDER']
        self.playbook = getattr(package, 'playbook', None)
        self.script = getattr(package, 'script', None)
        self.shell = getattr(package, 'shell', None)
        self.git = getattr(package, 'git', None)
        self.artifacts = getattr(package, 'artifacts')
        self.options = getattr(package, 'ansible_options', None)
        self.ignorerc = getattr(package, 'ignore_rc', False)
        self.validrc = getattr(package, 'valid_rc', None)

        self.injector = DataInjector(self.all_hosts)

        self.ans_service = AnsibleService(self.config, self.hosts, self.all_hosts, self.options)

        self.ans_verbosity = get_ans_verbosity(self.config)

        self.ans_extra_vars = collections.OrderedDict(hosts=self.ans_service.inv.group)

        # attribute defining overall status of test execution. why is this
        # needed? when a test fails we handle the exception raised and call
        # the method to archive test artifacts. once fetching artifacts is
        # finished this status is used to fail carbon (if needed)
        self.status = 0

    def validate(self):
        """Validate."""
        raise NotImplementedError

    def __git__(self):

        self.status = self.ans_service.run_git_playbook(self.git)
        if self.status != 0:
            raise CarbonExecuteError('Failed to clone git repositories!')

    def __shell__(self):
        self.logger.info('Executing shell commands:')
        for index, shell in enumerate(self.shell):

            result = self.ans_service.run_shell_playbook(shell)

            ignorerc = self.ignorerc
            validrc = self.validrc

            if "ignore_rc" in shell and shell['ignore_rc']:
                ignorerc = shell['ignore_rc']
            elif "valid_rc" in shell and shell['valid_rc']:
                validrc = shell['valid_rc']

            if ignorerc:
                self.logger.info("Ignoring the rc for: %s" % shell['command'])

            elif validrc:
                if result['rc'] not in validrc:
                    self.status = 1
                    self.logger.error('Shell command %s failed. Host=%s rc=%d Error: %s'
                                      % (shell['command'], result['host'], result['rc'], result['err']))

            else:
                if result['rc'] != 0:
                    self.status = 1
                    self.logger.error('Shell command %s failed. Host=%s rc=%d Error: %s'
                                      % (shell['command'], result['host'], result['rc'], result['err']))

            if self.status == 1:
                raise ArchiveArtifactsError('Script %s failed to run successfully!' % shell['name'])
            else:
                self.logger.info('Successfully executed command : %s' % shell['command'])

    def __script__(self):
        self.logger.info('Executing scripts:')
        for index, script in enumerate(self.script):

            result = self.ans_service.run_script_playbook(script)

            ignorerc = self.ignorerc
            validrc = self.validrc

            if "ignore_rc" in script and script['ignore_rc']:
                ignorerc = script['ignore_rc']
            elif "valid_rc" in script and script['valid_rc']:
                validrc = script['valid_rc']

            if ignorerc:
                self.logger.info("Ignoring the rc for: %s" % script['name'])

            elif validrc:

                if result['rc'] not in validrc:
                    self.status = 1
                    self.logger.error('Script %s failed. Host=%s rc=%d Error: %s'
                                      % (script['name'], result['host'], result['rc'], result['err']))
            else:
                if result['rc'] != 0:
                    self.status = 1
                    self.logger.error('Script %s failed. Host=%s rc=%d Error: %s'
                                      % (script['name'], result['host'], result['rc'], result['err']))
            if self.status == 1:
                raise ArchiveArtifactsError('Script %s failed to run '
                                            'successfully!' % script['name'])
            else:
                self.logger.info('Successfully executed script : %s' % script['name'])

    def __playbook__(self):
        self.logger.info('Executing playbooks:')
        for index, playbook in enumerate(self.playbook):

            results = self.ans_service.run_playbook(playbook)

            ignorerc = self.ignorerc
            if "ignore_rc" in playbook and playbook['ignore_rc']:
                ignorerc = playbook['ignore_rc']

            if ignorerc:
                self.logger.info("Ignoring the rc for: %s"
                                 % playbook['name'])
            elif results[0] != 0:
                self.status = 1
                raise ArchiveArtifactsError('Playbook %s failed to run successfully!' % playbook['name'])
            else:
                self.logger.info('Successfully executed playbook : %s' % playbook['name'])

    def __artifacts__(self):
        """Archive artifacts produced by the tests.

        This method takes a string formatted playbook, writes it to disk,
        provides the test artifacts details to the playbook and runs it. The
        result is on the machine where carbon is run, all test artifacts will
        be archived inside the data folder.

        Example artifacts archive structure:

        artifacts/
            host_01/
                test_01_output.log
                results/
                    ..
            host_02/
                test_01_output.log
                results/
                    ..
        """

        # local path on disk to save artifacts
        destination = os.path.join(self.config.get('RESULTS_FOLDER'), 'artifacts')

        # create artifacts location (if needed)
        if not os.path.exists(destination):
            os.makedirs(destination)

        self.logger.info('Fetching test artifacts @ %s' % destination)

        artifact_location = {}

        # settings required by synchronize module
        os.environ['ANSIBLE_LOCAL_TEMP'] = '$HOME/.ansible/tmp'
        os.environ['ANSIBLE_REMOTE_TEMP'] = '$HOME/.ansible/tmp'

        # setting variable so to no display any skipped tasks
        os.environ['DISPLAY_SKIPPED_HOSTS'] = 'False'

        # set extra vars
        extra_vars = copy.deepcopy(self.ans_extra_vars)
        extra_vars['dest'] = destination
        extra_vars['artifacts'] = self.artifacts

        # check for localhost in the list of host
        extra_vars['localhost'] = False
        if self._hosts:
            for h in self._hosts:
                if is_host_localhost(h.ip_address):
                    extra_vars['localhost'] = True
        else:
            extra_vars['localhost'] = True

        results = self.ans_service.run_artifact_playbook(extra_vars)

        if results[0] != 0:
            self.logger.error(results[1])
            raise CarbonExecuteError('A failure occurred while trying to copy '
                                     'test artifacts.')

        # Get results from file
        try:
            with open('sync-results.txt') as fp:
                lines = fp.read().splitlines()
        except (IOError, OSError) as ex:
            self.logger.error(ex)
            raise CarbonExecuteError('Failed to find the sync-results.txt file '
                                     'which means there was an uncaught failure running '
                                     'the synchronization playbook. Please enable verbose Ansible '
                                     'logging in the carbon.cfg file and try again.')

        # Build Results
        sync_results = []
        for line in lines:
            host, artifact, dest, skipped, rc = ast.literal_eval(textwrap.dedent(line).strip())
            sync_results.append({'host': host, 'artifact': artifact, 'destination': dest, 'skipped': skipped, 'rc': rc})

        # remove Sync Results file
        os.remove('sync-results.txt')

        for r in sync_results:
            if r['rc'] != 0 and not r['skipped']:
                self.logger.error('Failed to copy the artifact(s), %s, from %s' % (r['artifact'], r['host']))
            if r['rc'] == 0 and not r['skipped']:
                temp_list = r['artifact'].replace('[', '').replace(']', '').replace("'", "").split(',')
                if not extra_vars['localhost']:
                    art_list = [a[11:] for a in temp_list if 'cd+' not in a]
                    path = '/'.join(r['destination'].split('/')[-3:])
                else:
                    path = '/'.join(r['destination'].split('/')[2:-1])
                    art_list = ['/'.join(a.replace('’', "").split('->')[-1].split('/')[4:]) for a in temp_list]

                self.logger.info('Copied the artifact(s), %s, from %s' % (art_list, r['host']))

                # Update the execute resource with the location of artifacts

                if path in artifact_location:
                    current_list = artifact_location.get(path)
                    current_list.extend(art_list)
                    artifact_location.update({path: current_list})
                else:
                    artifact_location[path] = art_list

            if self.execute.artifact_locations:
                self.execute.artifact_locations.update(artifact_location)
            else:
                self.execute.artifact_locations = artifact_location

            if r['skipped']:
                self.logger.warning('Could not find artifact(s), %s, on %s. Make sure the file exists '
                                    'and defined properly in the definition file.' % (r['artifact'], r['host']))

    def run(self):
        """Run.

        The run method is the main entry point for the runner executor. This
        method will invoke various other methods in order to successfully
        run the runners execute types given.
        """
        for attr in ['git', 'shell', 'playbook', 'script', 'artifacts']:
            # skip if the execute resource does not have the attribute defined
            if not getattr(self, attr):
                continue

            # call the method associated to the execute resource attribute
            try:
                getattr(self, '__%s__' % attr)()
            except (ArchiveArtifactsError, CarbonExecuteError, AnsibleServiceError) as ex:
                # test execution failed, test artifacts may still have been
                # generated. lets go ahead and archive these for debugging
                # purposes
                self.logger.error(ex.message)
                if (attr != 'git' or attr != 'artifacts') and self.artifacts is not None:
                    self.logger.info('Fetching test generated artifacts')
                    self.__artifacts__()

                if self.status:
                    raise CarbonExecuteError('Test execution failed to run '
                                             'successfully!')
