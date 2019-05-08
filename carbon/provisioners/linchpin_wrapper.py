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

from os import path, environ, pardir, makedirs
import sys
import errno
import yaml
try:
    from linchpin import LinchpinAPI
    from linchpin.context import LinchpinContext
except ImportError:
    pass
from carbon.core import CarbonProvisioner
from carbon.exceptions import CarbonProvisionerError, CarbonProviderError
import json


class Logger(object):
    # redirect stdout (and thus print() function) to logfile *and* terminal
    # http://stackoverflow.com/a/616645
    def __init__(self, logger):
        self.stdout = sys.stdout
        self.logger = logger
        sys.stdout = self

    def __del__(self):
        sys.stdout = self.stdout

    def write(self, message):
        self.logger.info(message)

    def flush(self):
        pass


class LinchpinWrapperProvisioner(CarbonProvisioner):
    __provisioner_name__ = 'linchpin-wrapper'

    def __init__(self, host):
        super(LinchpinWrapperProvisioner, self).__init__(host)
        self.data_folder = path.realpath(getattr(host, 'data_folder'))
        self.linchpin_api = LinchpinAPI(self._init_context())
        self.linchpin_api.setup_rundb()
        self._create_pinfile()
        self._load_credentials()

    def _init_context(self):
        context = LinchpinContext()
        context.setup_logging()
        context.load_config()
        context.load_global_evars()
        results_dir = path.abspath(path.join(self.data_folder, pardir,
                                             '.results'))
        if path.exists(results_dir):
            lws_path = path.join(results_dir, 'linchpin')
        else:
            lws_path = path.join(self.data_folder, 'linchpin')
        context.set_cfg('lp', 'workspace', lws_path)
        context.set_evar('workspace', lws_path)
        context.set_cfg('lp', 'distill_data', True)
        context.set_evar('generate_resources', False)
        context.set_evar('debug_mode', True)
        return(context)

    def _load_credentials(self):
        # Linchpin supports Openstack environment variables
        # https://linchpin.readthedocs.io/en/latest/openstack.html#credentials-management
        # It is better to keep the credentials in memory
        # This is also reduce complexity by not calling openstack directly
        if self.provider == 'openstack':
            environ['OS_USERNAME'] = self.provider_credentials['username']
            environ['OS_PASSWORD'] = self.provider_credentials['password']
            environ['OS_AUTH_URL'] = self.provider_credentials['auth_url']
            environ['OS_PROJECT_NAME'] = self.provider_credentials['tenant_name']
            if 'domain_name' in self.provider_credentials:
                environ['OS_DOMAIN_NAME'] = self.provider_credentials['domain_name']
        elif self.provider == 'beaker':
            bkr_conf = path.join(path.abspath(self.data_folder), 'beaker.conf')
            environ['BEAKER_CONF'] = bkr_conf
            creds = self.provider_credentials
            with open(bkr_conf, 'w') as conf:
                if 'hub_url' in self.provider_credentials:
                    conf.write('HUB_URL = "%s"\n' % creds['hub_url'])
                if 'ca_path' in self.provider_credentials:
                    conf.write('CA_CERT = "%s"\n' % creds['ca_path'])
                if 'password' in self.provider_credentials:
                    conf.write('AUTH_METHOD = "password"\n')
                    conf.write('USERNAME = "%s"\n' % creds['username'])
                    conf.write('PASSWORD = "%s"\n' % creds['password'])
                elif 'keytab' in self.provider_credentials:
                    conf.write('AUTH_METHOD = "krbv"\n')
                    conf.write('KRB_PRINCIPAL = "%s"\n' % creds['keytab_principal'])
                    conf.write('KRB_KEYTAB = "%s"\n' % creds['keytab'])
                    if 'realm' in self.provider_credentials:
                        conf.write('KRB_REALM = "%s"\n' % creds['realm'])
                    if 'service' in self.provider_credentials:
                        conf.write('KRB_SERVICE = "%s"\n' % creds['service'])
                    if 'ccache' in self.provider_credentials:
                        conf.write('KRB_CCACHE = "%s"\n' % creds['ccache'])
        else:
            raise CarbonProvisionerError('No credentials provided')

    def _create_pinfile(self):
        tpath = path.abspath(path.join(path.dirname(__file__), pardir, "files",
                                       "PinFile.yml"))
        with open(tpath, 'r') as template:
            pindict = yaml.load(template)
        if self.provider == 'openstack':
            resource_def = {
                'role': 'os_server',
                'count': 1,
                'verify': 'false',
                'name': getattr(self.host, 'name', 'carbon-name'),
            }
            for key, value in self.provider_params.items():
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
        elif self.provider == 'beaker':
            resource_def = {
                'role': 'bkr_server'
            }
            recipeset = {}
            for key, value in self.provider_params.items():
                if key in ['distro', 'arch', 'variant', 'name',
                           'taskparam', 'priority']:
                    recipeset[key] = value
                elif key == 'whiteboard':
                    resource_def['whiteboard'] = value
                elif key == 'jobgroup':
                    resource_def['job_group'] = value
                elif key == 'host_requires_options':
                    hostrequires = []
                    for hq in value:
                        hostrequires.append({
                            "tag": hq.split(" ")[0],
                            "op": hq.split(" ")[1],
                            "value": hq.split(" ")[2]
                        })
                    recipeset['hostrequires'] = hostrequires
                elif key == 'tags':
                    if value.size > 1:
                        raise CarbonProviderError('Only one tag == supported')
                    else:
                        recipeset['tags'] = value[0]
                elif key == 'node_id':
                    recipeset['ids'] = value
                elif key == 'ssh_key':
                    recipeset['ssh_key'] = [value]
            resource_def['recipesets'] = [recipeset]
            resource_grp = {
                'resource_group_name': 'carbon',
                'resource_group_type': 'beaker',
                'resource_definitions': [resource_def]
            }
            pindict['carbon']['topology']['resource_groups'] = [resource_grp]
            pindict['carbon']['layout']['inventory_layout']['vars'].update(
                getattr(self.host, 'ansible_params'))
            self.pinfile = pindict
        else:
            raise CarbonProviderError("Unknown provider %s" % self.provider)
        self.logger.info('Generated PinFile:\n%s' % yaml.dump(pindict))

    def _create_inventory(self, results):
        inv = self.linchpin_api.generate_inventory(
            resource_data=results['carbon']['outputs']['resources'],
            layout=results['carbon']['inputs']['layout_data']['inventory_layout'],
            topology_data=results['carbon']['inputs']['topology_data']
        )
        self.logger.debug(inv)
        inv_path = path.join(self.data_folder, 'inventory')
        try:
            makedirs(path.dirname(inv_path))
        except OSError as exc:
            if exc.errno == errno.EEXIST and path.isdir(path.dirname(inv_path)):
                pass
            else:
                raise
        with open(inv_path, 'w+') as inv_file:
            inv_file.write(inv)

    def _create(self):
        host = getattr(self.host, 'name', 'carbon-name')
        Log = Logger(logger=self.logger)
        code, results = self.linchpin_api.do_action(self.pinfile, action='up')
        del Log
        self.logger.debug(json.dumps(results))
        if code:
            raise CarbonProvisionerError("Failed to provision host %s" % host)
        self.logger.info('Successfully created host %s' % host)
        results = self.linchpin_api.get_run_data(
            list(results)[0], ('inputs', 'outputs'))
        self._create_inventory(results)
        resource = results['carbon']['outputs']['resources']
        if self.provider == 'openstack':
            os_server = resource[0]['servers'][0]
            _ip = os_server['interface_ip']
            _id = os_server['id']
        if self.provider == 'beaker':
            bkr_server = resource[0]
            _ip = bkr_server['system']
            _id = bkr_server['id']
            getattr(self.host, 'provider_params')['job_url'] = bkr_server['url']

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
        Log = Logger(logger=self.logger)
        self.linchpin_api.do_action(self.pinfile, action='destroy')
        del Log
        self.logger.info('Successfully deleted host %s.' % host)
