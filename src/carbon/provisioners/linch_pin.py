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
    carbon.provisioners.linchpin

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import ast
import json
import os
import shutil
import yaml

from distutils import dir_util
# from linchpin.cli.context import LinchpinContext
# from linchpin.api import LinchpinAPI
from ..constants import CARBON_ROOT
from ..core import CarbonProvisioner
from ..helpers import file_mgmt


class LinchpinProvisioner(CarbonProvisioner):
    """This is the base class for Linch-pin provisioner to provision machines.
    It handles actions such as creating necessary files and calling Linch-pin
    directly by the API.
    """
    __provisioner_name__ = 'linchpin'
    _assets = ["pinfile", "credentials", "layout", "topology"]

    _topology = "topology.yml"
    _layout = "layout.yml"
    _pinfile = "PinFile"
    _credentials = "credentials.yml"
    _workspace = None
    _logspace = None
    _linchpin_context = None
    _linchpin = None

    def __init__(self, host_desc):
        """Constructor.

        Each time a linch-pin provisioner class is instantiated it will
        perform the following tasks:

        1. Initialize linch-pin directory structure and setup linch-pin ctx.
        2. Create topology file.
        3. Create layout file.
        4. Create pin file.
        5. Create credentials file.

        :param host_desc: A host description in (dict form) based on a Carbon
            host object.
        """
        super(LinchpinProvisioner, self).__init__()
        self.host_desc = host_desc
        self.init()
        self.create_topology_file()
        self.create_layout_file()
        self.create_pin_file()
        self.create_credentials_file()

    def init(self):
        """Create the linch-pin directory structure to provision and teardown
        resources. It uses the initialization command from linch-pin.

        http://linch-pin.readthedocs.io/en/latest/config_general.html#initialization
        """
        # Set linch-pin workspace
        self._workspace = os.path.join(CARBON_ROOT, "jobs",
                                       self.host_desc['scenario_id'])
        # Set linch-pin logspace
        self._logspace = os.path.join(CARBON_ROOT, "jobs",
                                      self.host_desc['scenario_id'], "logs")
        if not os.path.exists(self._logspace):
            os.makedirs(self._logspace)

        # Create linch-pin context object
        # self._linchpin_context = LinchpinContext()
        self._linchpin_context = None
        self._linchpin_context.load_config()
        self._linchpin_context.load_global_evars()
        self._linchpin_context.cfgs['logger']['file'] = self._logspace + "/linchpin.log"
        self._linchpin_context.setup_logging()
        self._linchpin_context.workspace = self._workspace
        self._linchpin_context.log_info(
            "ctx.workspace: {0}".format(self._linchpin_context.workspace))
        self._linchpin_context.pinfile = self._linchpin_context.cfgs[
            'init']['pinfile']

        # Create linch-pin project/directory structure if does not exist
        if not os.path.exists(self._workspace) or \
                not os.path.exists(self._workspace + '/topologies') or \
                not os.path.exists(self._workspace + '/layouts') or \
                not os.path.exists(self._workspace + '/inventories'):
            self.lp_init()

        # Set absolute file paths for linch-pin files
        self._topology = os.path.join(self._workspace, "topologies",
                                      self.host_desc['name'] + ".yml")
        self._layout = os.path.join(self._workspace, "layouts",
                                    self.host_desc['name'] + "_layout.yml")
        self._pinfile = os.path.join(self._workspace, self._pinfile)
        # This file path gets updated in PinFile creation
        self._credentials = os.path.join(self._workspace,
                                         self.host_desc['provider'] + ".yml")

        # Set console
        self._linchpin_context.cfgs['ansible']['console'] = u'False'

        # Create linch-pin API object
        # self._linchpin = LinchpinAPI(self._linchpin_context)
        self._linchpin = None

    def lp_init(self):
        """
        Initializes a linchpin project, which generates an example PinFile, and
        creates the necessary directory structure for topologies and layouts.
        """

        ws = self._linchpin_context.workspace
        pf = self._linchpin_context.pinfile

        pf_w_path = os.path.realpath('{0}/{1}'.format(ws, pf))

        src = self._linchpin_context.cfgs['init']['source']
        src_w_path = os.path.realpath(
            '{0}/{1}'.format(self._linchpin_context.lib_path, src))

        src_pf = os.path.realpath('{0}.lp_example'.format(pf_w_path))

        if os.path.exists(pf_w_path):
            raise Exception("Directory %s already exists" % pf_w_path)

        dir_util.copy_tree(src_w_path, ws, verbose=1)
        os.rename(src_pf, pf_w_path)

        self._linchpin_context.log_state('{0} and file structure created at {1}'.format(
            self._linchpin_context.pinfile, self._linchpin_context.workspace))

    def lp_process_output(self):
        """ Proccess linchpin output files in resources directory
        """
        resource_dir = self._linchpin_context.workspace + "/resources"
        tmp_dir = self._linchpin_context.workspace + "/tmp"

        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        for filename in os.listdir(resource_dir):
            if filename.endswith(".output") and self.host_desc['os_name'] in filename:
                res_file = resource_dir + "/" + filename
                with open(res_file, 'r') as s:
                    data = s.read()
                    data = data.replace('null', 'None').replace('false', 'False').replace('true', 'True')

                    res = ast.literal_eval(data)

                    for key, value in res.iteritems():
                        if "os_server_res" in key and value:
                            host_list = []
                            ip_list = []
                            for item in value:
                                for machine in item['openstack']:
                                    host_list.append(machine['name'])
                                    ip_list.append(machine['interface_ip'])
                                host_desc_m = self.host_desc
                                host_desc_m.update({"ip_address": ip_list})
                                host_desc_m.pop("provider_creds", None)
                                host_desc_m.pop("scenario_id", None)
                                host_update = {'provision': host_desc_m}

                        elif value:
                            raise NotImplementedError

                output_yaml = tmp_dir + "/" + self.host_desc['name'] + ".yaml"
                with open(output_yaml, 'w') as fp:
                    yaml.dump(host_update, fp, allow_unicode=True)

    def lp_check_results(self, results, module, console=False):
        """
        Takes linch-pin returned results and processes for success or failure.
        Logs results. If Failures logs errors.
        Updates status of resource and continues
        """
        failure_log = {}
        log_output = {}
        prov_resource_pass = True

        # Process results if console True
        # Results only return 0 for success non zero failure
        if console == u'True' or console == u'true':
            for target, result in results.items():
                if result == 0:
                    self._linchpin_context.log_info(
                        "MODULE [{0} TARGET [{1}] --- Success".format(module, target))
                else:
                    self._linchpin_context.log_info(
                        "MODULE [%s] TARGET [%s] --- Failed".format(module, target))
                    prov_resource_pass = False
            return prov_resource_pass

            # TODO Update resources status here
            # or throw exception and caller handles it.

        # Process results if console False
        else:
            task_ok = 0
            task_failed = 0
            task_changed = 0
            failures = []
            log_msgs = []

            # Process each task result for target
            for target, result in results.items():
                for task_result in result:

                    # Catalog Changed
                    if task_result._result['changed'] is True:
                        task_changed = task_changed + 1

                    # Output Task Info to log
                    self._linchpin_context.log_info(
                        "TASK [{0}: {1}] ***".format(task_result._task._role, task_result._task.name))

                    # Check if failed an obtain error
                    if 'failed' in task_result._result:
                        task_stderr = ""
                        task_stdout = ""
                        task_msg = ""
                        task_failed = task_failed + 1
                        if 'module_stderr' in task_result._result:
                            task_stderr = task_result._result['module_stderr']
                        if 'module_stdout' in task_result._result:
                            task_stdout = task_result._result['module_stdout']
                        if 'msg' in task_result._result:
                            task_msg = task_result._result['msg']
                        elif 'message' in task_result._result:
                            task_msg = task_result._result['message']
                        bfailure = 'TARGET: [%s]: HOST: [%s]: TASK [%s: %s] *** FAILED! => { "changed": %s,' % (
                            target, task_result._host,
                            task_result._task._role, task_result._task.name,
                            task_result._result['changed'])
                        efailure = ' "failed": %s, "module_stderr": %s, "module_stdout": %s, "msg": %s}' % (
                            task_result._result['failed'],
                            json.dumps(task_stderr),
                            json.dumps(task_stdout),
                            json.dumps(task_msg))
                        failure = "%s %s" % (bfailure, efailure)
                        failures.append(failure)
                        prov_resource_pass = False
                        stderrstr = ""
                        stdoutstr = ""
                        msgstr = ""
                        if 'module_stderr' in task_result._result:
                            stderrstr = json.dumps(task_result._result['module_stderr'])
                        if 'module_stdout' in task_result._result:
                            stdoutstr = json.dumps(task_result._result['module_stdout'])
                        if 'msg' in task_result._result:
                            json.dumps(task_result._result['msg'])
                        logstr = 'fatal: [{0}]: FAILED! => "changed": {1}, "failed": {2}, "module_stderr": "{3}", ' \
                                 '"module_stdout": "{4}", "msg": "{5}"'.format(
                                     task_result._host, task_result._result['changed'],
                                     task_result._result['failed'],
                                     stderrstr, stdoutstr, msgstr)
                        self._linchpin_context.log_info(logstr)
                    # Track Success (OK)
                    else:
                        task_ok = task_ok + 1

                        # Output task result to linchpin log
                        self._linchpin_context.log_info("ok: [{0}]".format(task_result._host))
                        if 'msg' in task_result._result:
                            self._linchpin_context.log_info('"msg": {0}'.format(
                                json.dumps(task_result._result['msg'])))
                        if 'results' in task_result._result and 'include' in task_result._result['results']:
                            self._linchpin_context.log_info('"included": {0}'.format(
                                                            json.dumps(task_result._result['results']['include'])))
                        if 'results' in task_result._result:
                            for item in task_result._result['results']:
                                if 'include' in item:
                                    self._linchpin_context.log_info('"included": {0}'.format(
                                        json.dumps(item['include'])))

                # Update failure log and db status of resource
                failure_log[target] = failures

                # TODO Update DB of resource status
                # Do here or throw exception and let caller handle
                # Success Failure etc.

                # Update Msg's for logger
                log_msg = "%s            : ok=%s    changed=%s    unreachable=%s    failed=%s" \
                    % (task_result._host, task_ok, task_changed, 0, task_failed)
                tstr = "PLAY RECAP for %s - TARGET [%s]" % (module, target)
                log_msgs.append(
                    "***** %s *********************************************************************" % tstr)
                log_msgs.append(log_msg)
                log_output[target] = log_msgs

            # Output Summary to linchpin log
            for target, msgs in log_output.iteritems():
                for msg in msgs:
                    self._linchpin_context.log_info(msg)
                if target in failure_log and len(failure_log[target]) > 0:
                    self._linchpin_context.log_info("     {0} Failures:".format(target))
                    failures = failure_log[target]
                    for failure in failures:
                        self._linchpin_context.log_info("          {0}".format(failure))

            return prov_resource_pass

    def create_topology_file(self):
        """Create the linch-pin topology file which contains resources to be
        provisioned or teardown.

        http://linch-pin.readthedocs.io/en/latest/config_general.html#topologies
        """
        func = None
        _provider = self.host_desc['provider']

        try:
            func = getattr(LinchpinFiles, "%s_topology" % _provider)
        except AttributeError:
            raise Exception("Linch-pin provisioner does not know how to "
                            "create topology for %s provider." % _provider)

        _data = func(host_desc=self.host_desc, creds=self._credentials)
        file_mgmt('w', self._topology, _data)

    def create_layout_file(self):
        """Create the linch-pin layout file. The layout file defines the
        structure of the Ansible inventory file generated.

        http://linch-pin.readthedocs.io/en/latest/config_general.html#layouts
        """
        _lcontent = {
            "inventory_layout": {
                "hosts": {
                    self.host_desc["name"]: {
                        "count": 1,
                        "host_groups":
                            [self.host_desc["role"]]
                    }
                }
            }
        }
        file_mgmt('w', self._layout, _lcontent)

    def create_pin_file(self):
        """Create the linch-pin pin file. The pin file defines the
        infrastructure to be provisioned or teardown.

        http://linch-pin.readthedocs.io/en/latest/config_general.html#pinfile
        """
        _target = {}
        _topology = os.path.splitext(self._topology)
        _layout = os.path.splitext(self._layout)
        _tmp_file = self._pinfile + ".yml"

        _target[self.host_desc['name']] = {
            "topology": _topology[0].split('/')[-1] + _topology[1],
            "layout": _layout[0].split('/')[-1] + _layout[1]
        }

        if os.path.exists(self._pinfile):
            shutil.move(self._pinfile, _tmp_file)
            pcontent = file_mgmt('r', _tmp_file)
            for target in pcontent:
                _target[target] = pcontent[target]

        _tmp_file = self._pinfile + ".yml"
        file_mgmt('w', _tmp_file, _target)
        shutil.move(_tmp_file, self._pinfile)

    def create_credentials_file(self):
        """Create the linch-pin credentials file."""
        func = None
        _provider = self.host_desc['provider']

        try:
            func = getattr(LinchpinFiles, "%s_creds" % _provider)
        except AttributeError:
            raise Exception("Linch-pin provisioner does not know how to "
                            "create creds for %s provider." % _provider)

        _data = func(host_desc=self.host_desc)

        # TODO: Should check if this file path for linchpin exists, some
        # providers may not have a credentials directory.
        self._credentials = os.path.join(self._linchpin_context.lib_path,
                                         "provision/roles/%s/vars" % _provider,
                                         _provider + ".yml")
        file_mgmt('w', self._credentials, _data)

    def _up(self):
        """Linch-pin up to provision resources.

        http://linch-pin.readthedocs.io/en/latest/linchpincli_linchpin_rise.html
        """
        # TODO: Need to submit a code patch to linch-pin to return output
        # TODO: Parse output depending on results
        # TODO: Handle if failure occured, do we need to destroy machines?
        results = self._linchpin.lp_up(self._pinfile, targets=(
            self.host_desc['name'],))
        result = self.lp_check_results(results, "lp_up",
                                       self._linchpin_context.cfgs['ansible']['console'])
        self.lp_process_output()

        # TODO: Remove this destroy call at somepoint, added for testing
        self._destroy()

        return result

    def _destroy(self):
        """Linch-pin destroy to teardown resources.

        http://linch-pin.readthedocs.io/en/latest/linchpincli_linchpin_drop.html
        """
        # TODO: Need to submit a code patch to linch-pin to return output
        # TODO: Parse output depending on results
        # TODO: Handle if failure occured, do we need to destroy machines?
        results = self._linchpin.lp_destroy(self._pinfile, targets=(
            self.host_desc['name'],))
        return self.lp_check_results(results, "lp_destroy",
                                     self._linchpin_context.cfgs['ansible']['console'])

    def create(self):
        """The main method to start resource creation. It will call linch-pin
        rise command.
        """
        self.logger.info('Provisioning machines from %s', self.__class__)
        if not self._up():
            raise Exception("Failed to provision resources. Check logs or job resources status's")

    def delete(self):
        """The main method to start resource deletion. It will call linch-pin
        drop command.
        """
        self.logger.info('Tearing down machines from %s', self.__class__)
        if not self._destroy():
            raise Exception("Failed to tear down all provisioned resources. Check logs or job resources status's")


class LinchpinFiles(object):
    """This class will generate the files necessary for linch-pin.Each
    linch-pin supported provider and supported by Carbon, will have an
    associated method which will create the necessary data.
    """

    @classmethod
    def openstack_topology(cls, **kwargs):
        """Create the linch-pin openstack provider topology data structure.
        :param kwargs: Required data to create topology.
        :return: Topology data structure.
        """
        _host_desc = kwargs['host_desc']
        _creds = os.path.splitext(kwargs['creds'])

        _res = {
            "topology_name": _host_desc['os_name'],
            "site": "qeos",
            "resource_groups": [
                {
                    "resource_group_name": _host_desc['os_name'],
                    "res_group_type": _host_desc['provider'],
                    "assoc_creds": _creds[0].split('/')[-1],
                    "res_defs": [
                        {
                            "count": _host_desc['os_count'],
                            "fip_pool": _host_desc['os_floating_ip_pool'],
                            "flavor": _host_desc['os_flavor'],
                            "image": _host_desc['os_image'],
                            "keypair": _host_desc['os_keypair'],
                            "networks": _host_desc['os_networks'],
                            "res_name": _host_desc['os_name'],
                            "res_type": "os_server"
                        }
                    ]
                }
            ]
        }

        return _res

    @classmethod
    def beaker_topology(cls, **kwargs):
        """Create the linch-pin beaker provider topology data structure.
        :param kwargs: Required data to create topology.
        :return: Topology data structure.
        """
        _host_desc = kwargs['host_desc']

        if _host_desc:
            raise NotImplementedError

        # TODO: Update base skeleton for a beaker resource with correct values
        _res = {
            "topology_name": _host_desc['name'],
            "resource_groups": [
                {
                    "resource_group_name": _host_desc['name'],
                    "res_group_type": _host_desc['provider'],
                    "job_group": None,
                    "recipesets": [
                        {
                            "count": None,
                            "distro": None,
                            "arch": _host_desc['bkr_arch'],
                            "arches": None,
                            "hostrequire": None,
                            "keyvalue": None
                        }
                    ]
                }
            ]
        }

        return _res

    @classmethod
    def openshift_topology(cls, **kwargs):
        """Create the linch-pin openshift provider topology data structure.
        :param kwargs: Required data to create topology.
        :return: Topology data structure.
        """
        _host_desc = kwargs['host_desc']

        if _host_desc:
            raise NotImplementedError

    @classmethod
    def openstack_creds(cls, **kwargs):
        """Create the linch-pin openshift provider topology data structure.
        :param kwargs: Required data to create credentials.
        :return: Topology data structure.
        """
        _host_desc = kwargs['host_desc']
        mydict = {}
        mydict["endpoint"] = _host_desc["provider_creds"]["auth_url"]
        mydict["project"] = _host_desc["provider_creds"]["tenant_name"]
        mydict["username"] = _host_desc["provider_creds"]["username"]
        mydict["password"] = _host_desc["provider_creds"]["password"]
        return mydict

    @classmethod
    def beaker_creds(cls, **kwargs):
        """Create the linch-pin beaker provider topology data structure.
        :param kwargs: Required data to create credentials.
        :return: Topology data structure.
        """
        _host_desc = kwargs['host_desc']

        if _host_desc:
            raise NotImplementedError

    @classmethod
    def openshift_creds(cls, **kwargs):
        """Create the linch-pin openshift provider topology data structure.
        :param kwargs: Required data to create credentials.
        :return: Topology data structure.
        """
        _host_desc = kwargs['host_desc']

        if _host_desc:
            raise NotImplementedError
