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
import os
import shutil
import sys

from distutils import dir_util
from linchpin.api.utils import yaml2json
from linchpin.context import LinchpinContext
from linchpin.api import LinchpinAPI
from linchpin.api.invoke_playbooks import invoke_linchpin
from ..constants import CARBON_ROOT
from ..core import CarbonProvisioner
from ..helpers import file_mgmt


class lp_API(LinchpinAPI):

    def lp_up(self, pinfile, targets='all', console=True):
        """
        This function takes a list of targets, and provisions them according
        to their topology. If an layout argument is provided, an inventory
        will be generated for the provisioned nodes.

        \b
        pf:
            Provided PinFile, with available targets,

        \b
        targets:
            A tuple of targets to provision.
        """

        return(self.run_playbook(pinfile, targets, playbook="provision", console=console))

    def lp_destroy(self, pf, targets, console=True):
        """
        This function takes a list of targets, and performs a destructive
        teardown, including undefining nodes, according to the target.

        \b
        SEE ALSO:
            lp_down - currently unimplemented

        \b
        pf:
            Provided PinFile, with available targets,

        \b
        targets:
            A tuple of targets to destroy.
        """

        return(self.run_playbook(pf, targets, playbook="destroy", console=console))

    def run_playbook(self, pinfile, targets='all', playbook='provision', console=True):
        """
        This function takes a list of targets, and executes the given
        playbook (provison, destroy, etc.) for each provided target.

        \b
        pf:
            Provided PinFile, with available targets,

        \b
        targets:
            A tuple of targets to run.
        """

        results = []
        pf = yaml2json(pinfile)

        # playbooks check whether from_cli is defined
        # if not, vars get loaded from linchpin.conf
        self.ctx.evars['from_cli'] = True
        self.ctx.evars['lp_path'] = self.lp_path

        self.ctx.evars['default_resources_path'] = '{0}/{1}'.format(
            self.ctx.workspace,
            self.ctx.cfgs['evars']['resources_folder'])
        self.ctx.evars['default_inventories_path'] = '{0}/{1}'.format(
            self.ctx.workspace,
            self.ctx.cfgs['evars']['inventories_folder'])

        self.ctx.evars['state'] = "present"

        if playbook == 'destroy':
            self.ctx.evars['state'] = "absent"

        # checks wether the targets are valid or not
        if set(targets) == set(pf.keys()).intersection(targets) and len(targets) > 0:
            for target in targets:
                self.ctx.log_state('{0} target: {1}'.format(playbook, target))
                topology_registry = pf.get("topology_registry", None)
                self.ctx.evars['topology'] = self.find_topology(pf[target]["topology"],
                                                                topology_registry)
                if "layout" in pf[target]:
                    self.ctx.evars['layout_file'] = (
                        '{0}/{1}/{2}'.format(self.ctx.workspace,
                                             self.ctx.cfgs['evars'][
                                                 'layouts_folder'],
                                             pf[target]["layout"]))


#                def invoke_linchpin(ctx, lp_path, self.ctx.evars, playbook='provision', console=True):
                # invoke the PROVISION linch-pin playbook
                output = invoke_linchpin(
                    self.ctx,
                    self.lp_path,
                    self.ctx.evars,
                    playbook=playbook,
                    console=console
                )
                results.append({target: output})
            return results

        elif len(targets) == 0:
            for target in set(pf.keys()).difference():
                self.ctx.log_state('{0} target: {1}'.format(playbook, target))
                topology_registry = pf.get("topology_registry", None)
                self.ctx.evars['topology'] = self.find_topology(pf[target]["topology"],
                                                                topology_registry)
                if "layout" in pf[target]:
                    self.ctx.evars['layout_file'] = (
                        '{0}/{1}/{2}'.format(self.ctx.workspace,
                                             self.ctx.cfgs['evars'][
                                                 'layouts_folder'],
                                             pf[target]["layout"]))

                # invoke the PROVISION linch-pin playbook
                output = invoke_linchpin(
                    self.ctx,
                    self.lp_path,
                    self.ctx.evars,
                    playbook=playbook,
                    console=console
                )
                results.append({target: output})
            return results
        else:
            raise KeyError("One or more Invalid targets found")


class LinchpinProvisioner(CarbonProvisioner):
    """This is the base class for Linch-pin provisioner to provision machines.
    It handles actions such as creating necessary files and calling Linch-pin
    directly by the API.
    """
    _topology = "topology.yml"
    _layout = "layout.yml"
    _pinfile = "PinFile"
    _credentials = "credentials.yml"
    _workspace = None
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

        # Create linch-pin context object
        self._linchpin_context = LinchpinContext()
        self._linchpin_context.load_config()
        self._linchpin_context.load_global_evars()
        self._linchpin_context.setup_logging(
            eval(self._linchpin_context.cfgs['logger']['enable']))
        self._linchpin_context.workspace = self._workspace
        self._linchpin_context.log_info(
            "ctx.workspace: {0}".format(self._linchpin_context.workspace))
        self._linchpin_context.pinfile = self._linchpin_context.cfgs[
            'init']['pinfile']

        # Create linch-pin project/directory structure
        if not os.path.exists(self._workspace):
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

        # Create linch-pin API object
        self._linchpin = lp_API(self._linchpin_context)

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
            print "Directory already exists"
            sys.exit(10)

        dir_util.copy_tree(src_w_path, ws, verbose=1)
        os.rename(src_pf, pf_w_path)

        self._linchpin_context.log_state('{0} and file structure created at {1}'.format(
            self._linchpin_context.pinfile, self._linchpin_context.workspace))

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
        # TODO: Handle if failure occured, do we need to destory machines?
        results = self._linchpin.lp_up(self._pinfile, targets=(
            self.host_desc['name'],), console=False)
        print(results)

        # TODO: Remove this destory call at somepoint, added for testing
        self._destory()

    def _destory(self):
        """Linch-pin destroy to teardown resources.

        http://linch-pin.readthedocs.io/en/latest/linchpincli_linchpin_drop.html
        """
        # TODO: Need to submit a code patch to linch-pin to return output
        # TODO: Parse output depending on results
        # TODO: Handle if failure occured, do we need to destory machines?
        results = self._linchpin.lp_destroy(self._pinfile, targets=(
            self.host_desc['name'],), console=False)
        print(results)

    def create(self):
        """The main method to start resource creation. It will call linch-pin
        rise command.
        """
        print('Provisioning machines from {klass}'
              .format(klass=self.__class__))
        self._up()

    def delete(self):
        """The main method to start resource deletion. It will call linch-pin
        drop command.
        """
        print('Tearing down machines from {klass}'
              .format(klass=self.__class__))
        self._destory()


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
                            "keypair": _host_desc['os_key_name'],
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
        mydict["endpoint"] = _host_desc["creds"]["auth_url"]
        mydict["project"] = _host_desc["creds"]["tenant_name"]
        mydict["username"] = _host_desc["creds"]["username"]
        mydict["password"] = _host_desc["creds"]["password"]
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
