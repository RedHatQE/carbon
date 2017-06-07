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
import os
import random
import time
import yaml

from glanceclient.client import Client as glance_client
from keystoneauth1 import identity, session
from neutronclient.v2_0 import client as neutron_client
from novaclient.client import Client as nova_client
from novaclient.exceptions import NotFound, OverLimit

from ..core import CarbonException, CarbonProvisioner
from ..constants import CARBON_ROOT

MAX_WAIT_TIME = 100
ALPHA_LIST = 'abcdefghijklmnopqrstuvwxyz'


class OpenstackProvisionerException(CarbonException):
    """Base class for openstack provisioner exceptions."""
    pass


class InvalidParameter(OpenstackProvisionerException):
    """Base class for all invalid parameter exceptions."""
    pass


class OpenstackProvisioner(CarbonProvisioner):
    """
    Carbon's own openstack provisioner
    """
    __provisioner_name__ = 'openstack'
    __api_version__ = '2'

    _nova = None
    _neutron = None
    _glance = None
    _session = None

    def __init__(self, host):
        """Constructor.

        :param host: The host object.
        """
        super(OpenstackProvisioner, self).__init__()

        # host description
        self.host = host

        # Set os networks
        self._networks = self.get_networks(self.host.os_networks)

        # Set os image
        self._image = self.get_image(self.host.os_image)

        # Set os flavor
        self._flavor = self.get_flavor(self.host.os_flavor)

    @property
    def key_session(self):
        """Create a keystone authenticated session (when needed) and return
        keystone session object.

        :return: The keystone session object.
        """
        if not self._session:
            self._session = session.Session(
                auth=identity.v2.Password(
                    auth_url=self.host.provider.credentials['auth_url'],
                    tenant_name=self.host.provider.credentials['tenant_name'],
                    tenant_id=self.host.provider.credentials['tenant_id'],
                    username=self.host.provider.credentials['username'],
                    password=self.host.provider.credentials['password']
                )
            )
        return self._session

    @property
    def nova(self):
        """Instantiate novaclient (when needed) and return novaclient object.
        :return: The novaclient object
        """
        if not self._nova:
            self._nova = nova_client(
                self.__api_version__,
                session=self.key_session
            )
        return self._nova

    @property
    def glance(self):
        """Instantiate glanceclient (when needed) and return glanceclient
        object.
        :return: The glanceclient object.
        """
        if not self._glance:
            self._glance = glance_client(
                self.__api_version__,
                session=self.key_session
            )
        return self._glance

    @property
    def neutron(self):
        """Instantiate neutronclient (when needed) and return neutronclient
        object.
        :return: The neutronclient object.
        """
        if not self._neutron:
            self._neutron = neutron_client.Client(session=self.key_session)
        return self._neutron

    def _get_flavor(self, flavor_name):
        """Get desired flavor from nova client
        :param flavor_name: OS Flavor of resource specified in host resource description
        :return: The nova client flavor object
        :raises: InvalidParameter when flavor not found on nova client
        """
        try:
            return self.nova.flavors.find(name=flavor_name)
        except NotFound as ex:
            self.logger.error('Flavor %s not found or invalid.', flavor_name)
            self.logger.debug('Traceback: %s', ex)
            raise InvalidParameter

    def get_flavor(self, flavor_name):
        """Get flavor
        :param flavor_name: OS Flavor of resource specified in host description
        :return: Nova client flavor object
        """
        return self._get_flavor(flavor_name)

    def _get_image(self, image_name):
        """Get desired image from glance client
        :param image_name: OS image name of resource specified in host description
        :return: The glance client image object
        :raises: InvalidParameter when image not found on glance client
        """
        try:
            return self.nova.glance.find_image(image_name)
        except NotFound as ex:
            self.logger.error('Image %s not found or invalid.', image_name)
            self.logger.debug('Traceback: %s', ex)
            raise InvalidParameter

    def get_image(self, image_name):
        """Get image
        :param image_name: OS image name of resource specified in host descripiton
        :return: Glance client image object
        """
        return self._get_image(image_name)

    def _get_network(self, net_name):
        """Get desired network from neutron client
        :param net_name: Network name for resource specified in host description
        :return: The Neutron client network object
        :raises: InvalidParameter if network not found on neutron client
        """
        try:
            return self.nova.neutron.find_network(net_name)
        except NotFound as ex:
            self.logger.error('Network %s not found or invalid.', net_name)
            self.logger.debug('Traceback: %s', ex)
            raise InvalidParameter

    def get_networks(self, networks):
        """Get networks
        :param networks: List of network names for resource specified in host description
        :return: List of neutron client network objects
        """
        return [self._get_network(network_name) for network_name in networks]

    def _wait_for(self, label, condition, obj_getter, timeout_sec=120, wait_sec=1):
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
        self.logger.debug('%s - START', label)
        while not condition(obj):
            if (datetime.datetime.now() - start) > timeout:
                raise Exception(label, timeout_sec)
            time.sleep(wait_sec)
            obj = obj_getter()
        self.logger.debug('%s - DONE', label)
        return obj

    def _create_node(self,
                     name,
                     image,
                     flavor,
                     nics,
                     keypair,
                     userdata={},
                     max_attempts=3):
        """Create vm in openstack
        :param name: Name of vm
        :param image: Image to use to create vm
        :param flavor: Flavor of vm to create
        :param nics: NICS to configure for vm
        :param keypair:
        :param userdata: User data to configure on vm
        :param max_attempts: Number of tries to attempt to create vm
        :returns: Node object"""
        attempt = 1
        while attempt <= max_attempts:
            try:
                node = self.nova.servers.create(
                    name=name,
                    key_name=keypair,
                    image=image,
                    flavor=flavor,
                    nics=nics,
                    userdata=userdata)
                return node
            except OverLimit:
                self.logger.warn('Still not enough quota available for %s',
                                 name)
                wait_time = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('Attempt %s of %s, waiting for %s seconds.',
                                 attempt, max_attempts, wait_time)
                time.sleep(wait_time)

    def get_node_by_id(self, node_id):
        """Return the node object based on a node id.
        :return: Node object.
        """
        try:
            return self.nova.servers.get(node_id)
        except NotFound as ex:
            self.logger.warn('Unable to get node from node id: %s', node_id)
            self.logger.debug('Traceback: %s', ex)
            return None

    def get_node_by_name(self, node_name):
        """Return the node object based on a node name.
        :return: Node object.
        """
        for node in self.nova.servers.list():
            if node.name == node_name:
                return node
        return None

    def wait_for_nonexist_state(self, node):
        """Wait for node to be deleted and does not exist
        :param node: Node to teardown
        :return: Node object
        :raises: OpenstackProvisionerException
        """

        node = self._wait_till_node_not_deleting(node)
        if node is None:
            return node
        if node is not None:
            self.logger.error('Issue in deletion of node %s', node.name)
            raise OpenstackProvisionerException
        return node

    def wait_for_active_state(self, node):
        """Wait for created vm to be active
        :param: node to create on openstack
        :returns: Node object
        :raises: OpenstackProvisionerExecption
        """
        node = self._wait_till_node_not_building(node)
        if node is None:
            self.logger.error('Failed to boot node')
            raise OpenstackProvisionerException
        if node.status != 'ACTIVE' and node.status != 'ERROR':
            self.logger.error('Wrong status %s of node %s', node.status,
                              node.name)
        return node

    def _wait_till_node_not_building(self, node):
        """Wait for node to be done building
        :param node: Node building
        :returns: Node object
        """
        return self._wait_for(
            ('Waiting for end of BUILD state of %s' % node.name),
            lambda node: node.status != 'BUILD',
            lambda: self.get_node_by_id(node.id),
            timeout_sec=120)

    def _wait_till_node_not_deleting(self, node):
        """Wait for node to be done deleting. Does not exist
        :param node: Node being deleted
        :returns: Node object
        """
        return self._wait_for(
            ('Waiting for Delete to complete. End of DELETE state of %s' % node.name),
            lambda node: node is None,
            lambda: self.get_node_by_name(node.name),
            timeout_sec=300)

    def increase(self, s):
        new_s = []
        continue_change = True
        for c in s[::-1].lower():
            if continue_change:
                if c == 'z':
                    new_s.insert(0, 'a')
                else:
                    new_s.insert(0, ALPHA_LIST[ALPHA_LIST.index(c) + 1])
                    continue_change = False
            else:
                new_s.insert(0, c)

        return ''.join(new_s)

    def add_floating_ip(self, instance):
        """Add floating ip to instance
        :param instance: instance obj
        :returns: List of ips for resource"""

        float_ips = []

        try:
            instance_id = instance.id

            # Get Floating pool network info. For user supplied floating ip pool
            os_pools = self.neutron.list_networks(name=self.host.os_floating_ip_pool)

            for os_pool in os_pools['networks']:

                # Get port info for instance created
                os_ports = self.neutron.list_ports(device_id=instance_id)

                for os_port in os_ports['ports']:

                    # Create and add floating ip
                    float_ip = self.neutron.create_floatingip(
                        {'floatingip': {'floating_network_id': os_pool['id'],
                                        'port_id': os_port['id']}})
                    float_ips.append(float_ip)
        except:
            self.logger.error('Error assigning floating ip to host %s.' % str(instance.name))
            raise OpenstackProvisionerException

        return float_ips

    def update_host(self, instance, ip_list):
        """Update host with ip information and data

        :param instance: Instance object of resource
        :param ip_list: List of floating ips for resource
        """
        ips = []

        self.host.os_name = str(instance.name)
        self.host.os_node_id = str(instance.id)

        # Obtain list of ips
        for ip in ip_list:
            f_ip = str(ip['floatingip']['floating_ip_address'])
            ips.append(f_ip)
        self.host.os_ip_address = ips

    def create(self):
        """Create vm on openstack
        :returns: instance object
        :raises: Exception
        """
        error = False
        self.logger.info('Provisioning machines from %s', self.__class__)

        try:
            # Create instance on openstack
            instance = self._create_node(
                name=self.host.os_name,
                image=self._image,
                flavor=self._flavor,
                nics=[{'net-id': net.id} for net in self._networks],
                keypair=self.host.os_keypair)
        except:
            error = True
            self.logger.error('Error creating a host %s.' % self.host.os_name)

        try:
            # Wait for instance to be active
            self.wait_for_active_state(instance)

            # Add floating ip
            float_ips = self.add_floating_ip(instance)

            self.logger.info('Node %s created.' % str(instance.name))
        except OpenstackProvisionerException:
            error = True
            self.logger.error('Error activating/assigning ip to host %s.' % str(instance.name))

        # Update host object with useful information for user
        self.update_host(instance, float_ips)

        if error:
            self.logger.error('Error creating host/s.')
            self.logger.error('Failed to provision all resources. Check logs or '
                              'job resources status')
            raise Exception

    def delete(self):
        """Teardown vm on openstack
        :raises: Exception
        """
        self.logger.info('Tearing down machines from %s', self.__class__)
        try:
            server_exists = False
            node = self.get_node_by_name(self.host.os_name)
            if node:
                self.logger.debug("This server %s exists", self.host.os_name)
                server_exists = True

            if not server_exists:
                self.logger.info("server %s does not exist", self.host.os_name)
            else:
                self.logger.info("deleting server..........")

                # Get floating ips for networks
                floating_ips_dict = self.neutron.list_floatingips()
                floating_ips = [x['floating_ip_address'] for x in floating_ips_dict['floatingips']]

                # Get systems ips
                for host_network in self.host.os_networks:
                    # Get systems ips
                    sys_ips_dict = self.nova.servers.ips(node)
                    sys_ips = [x['addr'] for x in sys_ips_dict[host_network]]

                    # Get system floating ips
                    sys_floating_ips = [x for x in sys_ips if x in floating_ips]
                    sys_floating_ids = \
                        [y['id'] for x in sys_floating_ips for y
                         in floating_ips_dict['floatingips'] if x == y['floating_ip_address']]

                    # Disassociate and release floating ip
                    for fip in sys_floating_ids:
                        self.neutron.delete_floatingip(fip)

                self.nova.servers.delete(node)
                self.wait_for_nonexist_state(node)
                self.logger.info('Node %s deleted.', node.name)
        except OpenstackProvisionerException:
            self.logger.error('Error deleting host.')
            self.logger.error('Failed to tear down all provisioned resources. '
                              'Check logs or job resources status')
            raise Exception
