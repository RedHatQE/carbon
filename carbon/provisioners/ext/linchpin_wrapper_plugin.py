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
import sys
import errno
import os
import json
import stat
from os import path, environ, pardir, makedirs
from ..._compat import ConfigParser
try:
    from linchpin import LinchpinAPI
    from linchpin.context import LinchpinContext
except ImportError:
    pass
from carbon.core import ProvisionerPlugin
from carbon.exceptions import CarbonProvisionerError, CarbonProviderError
from ...helpers import LinchpinResourceBuilder, lookup_ip_of_hostname


class Logger(object):
    # redirect stdout (and thus print() function) to logfile *and* terminal
    # http://stackoverflow.com/a/616645
    def __init__(self, logger):
        self.stdout = sys.stdout
        self.logger = logger
        sys.stdout = self

    def __del__(self):
        # sys.stdout = self.stdout
        pass

    def write(self, message):
        self.logger.info(message)

    def flush(self):
        pass


class LinchpinWrapperProvisionerPlugin(ProvisionerPlugin):
    __plugin_name__ = 'linchpin-wrapper'

    def __init__(self, host):
        super(LinchpinWrapperProvisionerPlugin, self).__init__(host)
        self.data_folder = path.realpath(getattr(host, 'data_folder'))
        self.linchpin_api = LinchpinAPI(self._init_context())
        self.linchpin_api.setup_rundb()
        self._create_pinfile()
        self._load_credentials()
        self._create_inv = False

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
        if self.provider == 'libvirt' and self.provider_params.get('role', False) == 'libvirt_node':
            if self.provider_params.get('libvirt_become', None) is not None:
                context.set_evar('libvirt_become', str(self.provider_params.get('libvirt_become')))
            if self.provider_params.get('libvirt_image_path', False):
                context.set_evar('libvirt_image_path', self.provider_params.get('libvirt_image_path'))
            if self.provider_params.get('libvirt_user', False):
                context.set_evar('libvirt_user', self.provider_params.get('libvirt_user'))

        # setup the default_ssh_key_location to be the scenario workspace for libvirt and aws
        context.set_evar('default_ssh_key_path', os.path.join(
            os.path.abspath(getattr(self.host, 'workspace')), 'keys'))
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
                if 'ca_cert' in self.provider_credentials:
                    conf.write('CA_CERT = "%s"\n' % creds['ca_cert'])
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
        elif self.provider == 'libvirt':
            creds = self.provider_credentials
            if creds.setdefault('create_creds', False) and \
                    (creds.get('username', False) and creds.get('password', False)):
                if not path.exists(path.expanduser('~/.config/libvirt')):
                    os.makedirs(path.expanduser('~/.config/libvirt'))
                libvirt_auth = path.join(path.expanduser('~/.config/libvirt'), 'auth.conf')
                environ['LIBVIRT_AUTH_FILE'] = libvirt_auth
                if path.exists(libvirt_auth):
                    os.remove(libvirt_auth)
                config = ConfigParser()
                config.add_section('credentials-carbon')
                config.set('credentials-carbon', 'username', creds['username'])
                config.set('credentials-carbon', 'password', creds['password'])
                with open(libvirt_auth, 'w') as cfg:
                    config.write(cfg)
            else:
                self.logger.info('skipping creating libvirt credentials.')
        elif self.provider == 'aws':
            creds = self.provider_credentials
            if creds.setdefault('create_creds', False) and \
                    (creds.get('aws_access_key_id', False) and creds.get('aws_secret_access_key', False)):
                if not path.exists(path.expanduser('~/.aws/')):
                    os.makedirs(path.expanduser('~/.aws/'))
                aws_auth = path.join(path.expanduser('~/.aws/'), 'credentials')
                environ['AWS_PROFILE'] = 'Credentials'
                if path.exists(aws_auth):
                    os.remove(aws_auth)
                config = ConfigParser()
                config.add_section('Credentials')
                for k, v in creds.items():
                    if k != 'create_creds':
                        config.set('Credentials', k, v)
                with open(aws_auth, 'w') as cfg:
                    config.write(cfg)
            else:
                self.logger.info('skipping creating aws credentials.')
        else:
            raise CarbonProvisionerError('No credentials provided')

    def _create_pinfile(self):

        tpath = path.abspath(path.join(path.dirname(__file__), pardir, pardir, "files",
                                       "PinFile.yml"))
        with open(tpath, 'r') as template:
            pindict = yaml.safe_load(template)

        host_profile = self.host.profile()
        resource_def = LinchpinResourceBuilder.build_linchpin_resource_definition(
            getattr(self.host, 'provider'), host_profile)

        resource_grp = {
            'resource_group_name': 'carbon',
            'resource_group_type': self.provider,
            'resource_definitions': [resource_def]
        }
        pindict['carbon']['topology']['resource_groups'] = [resource_grp]
        pindict['carbon']['layout']['inventory_layout']['vars'].update(
            getattr(self.host, 'ansible_params'))
        pindict['carbon']['layout']['inventory_layout']['vars']['hostname'] = getattr(self.host, 'name')

        host_groups = ''
        try:
            host_groups = getattr(self.host, 'role')
        except AttributeError:
            try:
                host_groups = getattr(self.host, 'groups')
            except AttributeError:
                pass
        if host_groups:
            pindict['carbon']['layout']['inventory_layout']['hosts']['node']['host_groups'].extend(host_groups)

        self.logger.debug('Generated PinFile:\n%s' % yaml.dump(pindict))
        self.pinfile = pindict

        code, results = self.linchpin_api.do_validation(self.pinfile)
        if code != 0:
            self.logger.error('linchpin topology rc: %s' % code)
            self.logger.error(results)
            raise CarbonProvisionerError('Linchpin failed to validate pinfile.')

    def _create_inventory(self, results):
        inv = self.linchpin_api.generate_inventory(
            resource_data=results['carbon']['outputs']['resources'],
            layout=results['carbon']['inputs']['layout_data']['inventory_layout'],
            topology_data=results['carbon']['inputs']['topology_data']
        )
        self.logger.debug(inv)
        inv_path = path.join(self.data_folder, 'inventory')
        try:
            makedirs(inv_path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and path.isdir(path.dirname(inv_path)):
                pass
            else:
                raise
        full_path = path.join(inv_path, 'carbon-%s.inventory' % (getattr(self.host, 'name')))
        with open(full_path, 'w+') as inv_file:
            inv_file.write(inv)

    def _create(self):
        Log = Logger(logger=self.logger)
        host = getattr(self.host, 'name', 'carbon-name')
        code, results = self.linchpin_api.do_action(self.pinfile, action='up')
        del Log
        self.logger.debug(json.dumps(results))
        if code:
            raise CarbonProvisionerError("Failed to provision asset %s" % host)
        try:
            if getattr(self.host, 'provider_params')['count'] > 1:
                self.logger.info('Successfully created %s host resources'
                                 % getattr(self.host, 'provider_params')['count'])
            else:
                self.logger.info('Successfully created asset %s' % host)
        except KeyError:
            self.logger.info('Successfully created asset %s' % host)
        tx_id = list(results)[0]
        results = self.linchpin_api.get_run_data(
            tx_id, ('inputs', 'outputs'))
        # For now keeping this with carbon.
        if self._create_inv:
            self._create_inventory(results)

        resource = results['carbon']['outputs']['resources']

        # list of dicts to send back to host_provisioner
        res = list()
        if self.provider == 'openstack':
            for item in resource:
                for os_server in item['servers']:
                    ip_add = ""
                    if os_server.get('private_v4', False) != "" and os_server.get('public_v4', False) != "":
                        ip_add = dict(public=str(os_server.get('public_v4')),
                                      private=str(os_server.get('private_v4')))
                    else:
                        if os_server.get('private_v4', False) != "" and os_server.get('public_v4', False) == "":
                            ip_add = str(os_server['private_v4'])
                        if os_server.get('private_v4', False) == "" and os_server.get('public_v4', False) != "":
                            ip_add = str(os_server['public_v4'])

                    res.append({'ip': ip_add,
                                'node_id': os_server['id'],
                                'hostname': os_server['name'],
                                'tx_id': tx_id
                                })
        if self.provider == 'beaker':
            for bkr_server in resource:
                res.append({'ip': str(lookup_ip_of_hostname(bkr_server['system'])),
                            'node_id': bkr_server['id'],
                            'job_url': bkr_server['url'],
                            'hostname': bkr_server['system'].split('.')[0],
                            'tx_id': tx_id
                            })
        if self.provider == 'libvirt':
            # TODO update how multiple IPs are captured once Linchpin libvirt multinetwork fixed
            for lib_vm in resource:
                if self.provider_params.get('role', False) != 'libvirt_node':
                    del getattr(self.host, 'provider_params')['hostname']
                    res.append({'tx_id': tx_id})
                else:
                    res.append({'ip': str(lib_vm['ip']),
                                'hostname': lib_vm['name'],
                                'node_id': None,
                                'tx_id': tx_id
                                })
        if self.provider == 'aws':
            for aws_res in resource:
                if self.provider_params.get('role', False) != 'aws_ec2':
                    del getattr(self.host, 'provider_params')['hostname']
                    res.append({'tx_id': tx_id})

                if self.provider_params.get('role', False) == 'aws_ec2_key':
                    # the Linchpin resource generates the private key and dumps to the box
                    # but it doesn't change the permissions on it so it will fail when used
                    # later on during orchestrate/execute
                    key = os.path.join(os.path.join(getattr(self.host, 'workspace'), 'keys'),
                                       aws_res.get('key').get('name'))
                    if os.path.exists(key):
                        # set permission of the key
                        try:
                            os.chmod(key, stat.S_IRUSR | stat.S_IWUSR)
                        except OSError as ex:
                            raise CarbonProvisionerError(
                                'Error setting private key file permissions: %s' % ex
                            )
                if aws_res.get('instances'):
                    for instance in aws_res.get('instances'):
                        ip_add = ""
                        hostname = ""
                        if instance.get('private_ip', False) is not None \
                                and instance.get('public_ip', False) is not None:
                            ip_add = dict(public=str(instance.get('public_ip')),
                                          private=str(instance.get('private_ip')))
                            hostname = instance.get('public_dns_name')
                        else:
                            if instance.get('public_ip', False) is not None \
                                    and instance.get('private_ip', False) is None:
                                ip_add = str(instance.get('public_ip'))
                                hostname = instance.get('public_dns_name')
                            if instance.get('public_ip', False) is None \
                                    and instance.get('private_ip', False) is not None:
                                ip_add = str(instance.get('private_ip'))
                                hostname = instance.get('private_dns_name')
                        res.append({'ip': ip_add,
                                    'hostname': hostname,
                                    'node_id': str(instance.get('id')),
                                    'tx_id': tx_id
                                    })

        return res

    def create(self):
        """Create method. (must implement!)

        Provision the host supplied.
        """
        host = getattr(self.host, 'name')
        self.logger.info('Provisioning Asset %s in %s.' % (host, self.host.provider))
        res = self._create()
        # TODO change this log message to something else
        if res and res[-1].get('hostname', False):
            self.logger.info('Linchpin successfully provisioned %s asset(s) %s :'
                             % (len(res), [res[i]['hostname'] for i in range(0, len(res))]))
        else:
            self.logger.info('Linchpin successfully provisioned asset %s' % host)
        return res

    def delete(self):
        """Delete method. (must implement!)

        Teardown the host supplied.
        """
        host = getattr(self.host, 'name')
        try:
            txid = getattr(self.host, 'provider_params')['tx_id']
        except KeyError:
            txid = None
            self.logger.warning('No tx_id found for Asset: %s, this could mean it was not successfully'
                                ' provisioned. Attempting to perform the destroy without a tx_id'
                                ' but this might not work, so you may need to manually cleanup resources.' % host)
        self.logger.info('Delete Asset %s in %s.' % (host, self.provider))
        Log = Logger(logger=self.logger)
        self.linchpin_api.do_action(self.pinfile, action='destroy', tx_id=txid)
        del Log
        self.logger.info('Linchpin successfully deleted asset %s.' % host)

    def authenticate(self):
        raise NotImplementedError
