# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Red Hat, Inc.
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
    carbon.provisioners.ext.linchpin

    Integration module for Linchpin provisioner

    https://github.com/CentOS-PaaS-SIG/linchpin

    :copyright: (c) 2018 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

import yaml
from os import path, environ
from carbon.core import CarbonProvisioner
from carbon.exceptions import CarbonProviderError
from linchpin import LinchpinAPI
from linchpin.context import LinchpinContext


class LinchpinWrapperProvisioner(CarbonProvisioner):
    __provisioner_name__ = 'linchpin-wrapper'

    def __init__(self, host):
        super(LinchpinWrapperProvisioner, self).__init__(host)
        data_folder = path.realpath(getattr(host, 'data_folder'))
        self.context = LinchpinContext()
        self.context.setup_logging()
        self.context.load_config()
        self.context.load_global_evars()
        self.context.set_cfg('lp', 'workspace', "%s/linchpin" % data_folder)
        self.context.set_evar('workspace', "%s/linchpin" % data_folder)
        self.linchpin_api = LinchpinAPI(self.context)
        self.rundb = self.linchpin_api.setup_rundb()
        self._create_pinfile()
        self._load_credentials()
        self.linchpin_api.validate_topology(self.pinfile['carbon']['topology'])

    def _load_credentials(self):
        # Linchpin supports Openstack environment variables
        # https://linchpin.readthedocs.io/en/latest/openstack.html#credentials-management
        # It is better to keep the credentials in memory
        # This is also reduce complexity by not calling openstack directly
        environ['OS_USERNAME'] = self.provider_credentials['username']
        environ['OS_PASSWORD'] = self.provider_credentials['password']
        environ['OS_AUTH_URL'] = self.provider_credentials['auth_url']
        environ['OS_PROJECT_NAME'] = self.provider_credentials['tenant_name']

    def _create_pinfile(self):
        tpath = path.join(path.dirname(__file__), "..", "files", "PinFile.yml")
        with open(tpath, 'r') as template:
            pindict = yaml.load(template)
        if self.provider == 'openstack':
            resource_def = {
                'role': 'os_server',
                'count': 1,
                'verify': 'false',
                'name': getattr(self.host, 'name', 'carbon-name'),
            }
            for key, value in self.provider_params.iteritems():
                if key in ['flavor', 'image', 'keypair', 'networks']:
                    resource_def[key] = value
                elif key is 'floating_ip_pool':
                    resource_def['fip_pool'] = value
            resource_grp = {
                'resource_group_name': 'carbon',
                'resource_group_type': 'openstack',
                'resource_definitions': [resource_def]
            }
            pindict['carbon']['topology']['resource_groups'] = [resource_grp]
            pindict['carbon']['layout']['inventory_layout']['vars'].update(
                getattr(self.host, 'ansible_params'))
            self.pinfile = pindict
        self.logger.info('Generated PinFile:\n%s' % yaml.dump(pindict))

    def _create(self):
        host = getattr(self.host, 'name', 'carbon-name')
        code, results = self.linchpin_api.do_action(self.pinfile, action='up')
        if code:
            raise CarbonProviderError("Failed to provision host %s" % host)
        self.logger.info('Successfully created host %s' % host)
        results = self.linchpin_api.get_run_data(
            results.keys()[0], ('inputs', 'outputs'))
        results = results['carbon']['outputs']['resources']
        if self.provider == 'openstack':
            _ip = results['os_server_res'][0]['servers'][0]['interface_ip']
            _id = results['os_server_res'][0]['servers'][0]['id']
        return _ip, _id

    def create(self):
        """Create method. (must implement!)

        Provision the host supplied.
        """
        host = getattr(self.host, 'name')
        self.logger.info('Provisioning host %s in %s.' % (host, self.provider))
        _ip, _id = self._create()
        setattr(self.host, 'ip_address', str(_ip))
        getattr(self.host, 'provider_params')['node_id'] = str(_id)
        self.logger.info('Successfully provisioned host %s.' % host)

    def delete(self):
        """Delete method. (must implement!)

        Teardown the host supplied.
        """
        host = getattr(self.host, 'name')
        self.logger.info('Delete host %s in %s.' % (host, self.provider))
        self.linchpin_api.do_action(self.pinfile, action='destroy')
        self.logger.info('Successfully deleted host %s.' % host)
