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
    carbon.provisioners.openstack

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import datetime
import logging
import os
import time
import yaml
import random

from ..core import CarbonProvisioner
from ..constants import CARBON_ROOT
from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneclient.v2_0 import client as keystone_client
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
from novaclient import exceptions as nova_exceptions
from glanceclient import client as glance_client

LOG = logging.getLogger('service')
LOG.setLevel(logging.DEBUG)
fmtr = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(fmtr)
LOG.addHandler(sh)

VERSION = '2'
MAX_WAIT_TIME = 100


class ProvisionerException(Exception):
    pass


class ProviderException(Exception):
    pass


class HostException(Exception):
    pass


class ObjectNotFound(ProviderException):
    pass


class InvalidParameter(ProviderException):
    pass


class ForbiddenOperation(ProviderException):
    pass


def wait_for(label, condition, obj_getter, timeout_sec=120, wait_sec=1):
    """Wait for condition to be true until timeout.

    :param label: used for logging
    :param condition: function that takes the object from obj_getter and
        returns True or False
    :param obj_getter: function that returns the object on which the condition
        is tested
    :param timeout_sec: how many seconds to wait until a TimeoutError
    :param wait_sec: how many seconds to wait between testing the condition
    :raises: TimeoutError when timeout_sec is exceeded
             and condition isn't true
    """
    obj = obj_getter()
    timeout = datetime.timedelta(seconds=timeout_sec)
    start = datetime.datetime.now()
    LOG.debug('%s - START' % label)
    while not condition(obj):
        if (datetime.datetime.now() - start) > timeout:
            raise Exception(label, timeout_sec)
        time.sleep(wait_sec)
        obj = obj_getter()
    LOG.debug('%s - DONE' % label)
    return obj


class OpenstackProvisioner(CarbonProvisioner):
    """
    Carbon's own openstack provisioner
    """
    __provisioner_name__ = 'openstack'

    # connectors
    _nova = None
    _keystone = None
    _neutron = None
    _glance = None

    def __init__(self, host_desc):
        super(OpenstackProvisioner, self).__init__()
        self.host_desc = host_desc

        auth = v2.Password(auth_url=self.host_desc['provider_creds']['auth_url'],
                           tenant_name=self.host_desc['provider_creds']['tenant_name'],
                           tenant_id=self.host_desc['provider_creds']['tenant_id'],
                           username=self.host_desc['provider_creds']['username'],
                           password=self.host_desc['provider_creds']['password'],)
        self._session = session.Session(auth=auth)

        # initiate clients
        self._keystone = keystone_client.Client(session=self._session)
        # LOG.debug('Keystone client initialized')
        self._nova = nova_client.Client(VERSION, session=self._session)
        # LOG.debug('Nova client initialized')
        self._neutron = neutron_client.Client(session=self._session)
        # LOG.debug('Neutron client initialized')
        self._glance = glance_client.Client(VERSION, session=self._session)

        # LOG.debug('Glance client initialized')

        self._networks = self.get_networks(self.host_desc['os_networks'])

        self._image = self.get_image(self.host_desc['os_image'])

        self._flavor = self.get_flavor(self.host_desc['os_flavor'])

        # Set workspace
        self._workspace = os.path.join(CARBON_ROOT, "jobs",
                                       self.host_desc['scenario_id'])
        # Set logspace
        self._logspace = os.path.join(CARBON_ROOT, "jobs",
                                      self.host_desc['scenario_id'], "logs")
        # Create logs directory if needed
        if not os.path.exists(self._logspace):
            os.makedirs(self._logspace)

        # Set tmp directory if needed
        self._tmp = os.path.join(CARBON_ROOT, "jobs",
                                 self.host_desc['scenario_id'], "tmp")

        # Create tmp directory if needed
        if not os.path.exists(self._tmp):
            os.makedirs(self._tmp)

    def _get_flavor(self, flavor_name):
        try:
            return self._nova.flavors.find(name=flavor_name)
        except nova_exceptions.NotFound:
            LOG.error('Flavor {flavor_name} not found or invalid'
                      .format(flavor_name=flavor_name))
            raise InvalidParameter('Flavor {flavor_name} not found or invalid'
                                   .format(flavor_name=flavor_name))

    def get_flavor(self, flavor_name):
        return self._get_flavor(flavor_name)

    def _get_image(self, image_name):
        try:
            return self._nova.glance.find_image(image_name)
        except nova_exceptions.NotFound:
            LOG.error('Image {image_name} not found or invalid'
                      .format(image_name=image_name))
            raise InvalidParameter('Image {image_name} not found or invalid'
                                   .format(image_name=image_name))

    def get_image(self, image_name):
        return self._get_image(image_name)

    def _get_network(self, net_name):
        try:
            return self._nova.neutron.find_network(net_name)
        except nova_exceptions.NotFound:
            LOG.error('Network {net_name} not found or invalid'
                      .format(net_name=net_name))
            raise InvalidParameter('Network {net_name} not found or invalid'
                                   .format(net_name=net_name))

    def get_networks(self, networks):
        return [self._get_network(network_name) for network_name in networks]

    def _create_node(self,
                     name,
                     image,
                     flavor,
                     nics,
                     keypair,
                     userdata={},
                     max_attempts=3):
        attempt = 1
        while attempt <= max_attempts:
            try:
                node = self._nova.servers.create(
                    name=name,
                    key_name=keypair,
                    image=image,
                    flavor=flavor,
                    nics=nics,
                    userdata=userdata)
                return node
            except nova_exceptions.OverLimit:
                LOG.info('Still not enough quota available for {name}'
                         .format(name=name))
                wait_time = random.randint(10, MAX_WAIT_TIME)
                LOG.info('Attempt {attempt} of {max_attempts}'
                         'waiting for {wait_time} seconds'
                         .format(attempt=attempt,
                                 max_attempts=max_attempts,
                                 wait_time=wait_time))
                time.sleep(wait_time)

    def get_node_by_id(self, node_id):
        node = self._nova.servers.get(node_id)
        if node:
            return node
        return None

    def get_node_by_name(self, node_name):
        nodes = self._nova.servers.list()
        for node in nodes:
            name = getattr(node, 'name', None)
            if name == node_name:
                return node
        return None

    def wait_for_nonexist_state(self, node):
        node = self._wait_till_node_not_deleting(node)
        if node is None:
            return node
        if node is not None:
            raise ProvisionerException("Issue in deletion of node '%s'"
                                       % node.name)
        return node

    def wait_for_active_state(self, node):
        node = self._wait_till_node_not_building(node)
        if node is None:
            raise ProvisionerException("Failed to boot node")
        if node.status != 'ACTIVE' and node.status != 'ERROR':
            raise ProvisionerException("Wrong status '%s' of node '%s'"
                                       % (node.status, node.name))
        return node

    def _wait_till_node_not_building(self, node):
        return wait_for(
            ('Waiting for end of BUILD state of %s' % node.name),
            lambda node: node.status != 'BUILD',
            lambda: self.get_node_by_id(node.id),
            timeout_sec=120)

    def _wait_till_node_not_deleting(self, node):
        return wait_for(
            ('Waiting for Delete to complete. End of DELETE state of %s' % node.name),
            lambda node: node is None,
            lambda: self.get_node_by_name(node.name),
            timeout_sec=300)

    def create(self):
        LOG.info('Provisioning machines from {klass}'
                 .format(klass=self.__class__))
        instance = None
        try:
            instance = self._create_node(
                name=self.host_desc['os_name'],
                image=self._image,
                flavor=self._flavor,
                nics=[{'net-id': net.id} for net in self._networks],
                keypair=self.host_desc['os_keypair'])

            # Wait for system to be active
            self.wait_for_active_state(instance)

            # Add floating ip
            # Get Floating pool network info. For user supplied floating ip pool
            os_pools = self._neutron.list_networks(name=self.host_desc['os_floating_ip_pool'])
            os_pool = os_pools['networks'][0]

            # Get port info for instance created
            os_ports = self._neutron.list_ports(device_id=instance.id)
            os_port = os_ports['ports'][0]

            # Create and add floating ip
            float_ip = self._neutron.create_floatingip(
                {'floatingip': {'floating_network_id': os_pool['id'],
                                'port_id': os_port['id']}})

            # Add info to host
            host_desc_m = self.host_desc
            host_desc_m.update({"ip_address": "%s" % str(float_ip['floatingip']['floating_ip_address'])})
            host_desc_m.pop("provider_creds", None)
            host_desc_m.pop("scenario_id", None)
            host_desc_m["os_node_id"] = "%s" % str(instance.id)
            host_update = {'provision': host_desc_m}

            output_yaml = self._tmp + "/" + self.host_desc['name'] + ".yaml"
            with open(output_yaml, 'w') as fp:
                yaml.dump(host_update, fp, allow_unicode=True)

        except ProvisionerException:
            LOG.error('Error creating host.')
            raise Exception("Failed to provision resources. Check logs or job resources status's")

        LOG.info('Node %s created.' % self.host_desc['os_name'])
        return instance

    def delete(self):
        LOG.info('Tearing down machines from {klass}'
                 .format(klass=self.__class__))
        try:
            server_exists = False
            node = self.get_node_by_name(self.host_desc['os_name'])
            if node:
                LOG.debug("This server %s exists" % self.host_desc['os_name'])
                server_exists = True

            if not server_exists:
                LOG.info("server %s does not exist" % self.host_desc['os_name'])
            else:
                LOG.info("deleting server..........")

                # Get floating ips for networks
                floating_ips_dict = self._neutron.list_floatingips()
                floating_ips = [x['floating_ip_address'] for x in floating_ips_dict['floatingips']]

                # Get systems ips
                for host_network in self.host_desc['os_networks']:
                    # Get systems ips
                    sys_ips_dict = self._nova.servers.ips(node)
                    sys_ips = [x['addr'] for x in sys_ips_dict[host_network]]

                    # Get system floating ips
                    sys_floating_ips = [x for x in sys_ips if x in floating_ips]
                    sys_floating_ids = \
                        [y['id'] for x in sys_floating_ips for y
                         in floating_ips_dict['floatingips'] if x == y['floating_ip_address']]

                    # Disassociate and release floating ip
                    for x in sys_floating_ids:
                        self._neutron.delete_floatingip(x)

                self._nova.servers.delete(node)
                self.wait_for_nonexist_state(node)
                LOG.info('Node %s deleted.' % node.name)
        except ProvisionerException:
            LOG.error('Error deleting host.')
            raise Exception("Failed to tear down all provisioned resources. Check logs or job resources status's")
