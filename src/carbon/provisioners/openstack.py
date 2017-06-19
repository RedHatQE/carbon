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
import random
import time

from glanceclient.client import Client as Glance_client
from keystoneauth1 import identity, session
from neutronclient.v2_0 import client as neutron_client
from novaclient.client import Client as Nova_client
from novaclient.exceptions import ClientException, NotFound, OverLimit

from .._compat import string_types
from ..core import CarbonProvisioner, CarbonProvisionerException

MAX_WAIT_TIME = 100
MAX_ATTEMPTS = 3


class OpenstackProvisionerException(CarbonProvisionerException):
    """Base class for openstack provisioner exceptions."""

    def __init__(self, message):
        """Constructor.

        :param message: Details about the error.
        """
        self.message = message
        super(OpenstackProvisionerException, self).__init__(message)


class OpenstackProvisioner(CarbonProvisioner):
    """
    Carbon's own openstack provisioner
    """
    __provisioner_name__ = 'openstack'
    __api_version__ = '2'
    _assets = [""]

    def __init__(self, host):
        """Constructor.

        :param host: The host object.
        """
        super(OpenstackProvisioner, self).__init__()
        self.host = host

        # Define attributes assigned after constructor is initialized
        self._nova = None
        self._neutron = None
        self._glance = None
        self._session = None

    @property
    def name(self):
        """Return the name of the provisioner."""
        return self.__provisioner_name__

    @name.setter
    def name(self, value):
        """Raises an exception when trying to set the name for the provisioner
        after the class has been instantiated."""
        raise ValueError('You cannot set the name for the provisioner after '
                         'the class has been instantiated.')

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
            self._nova = Nova_client(
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
            self._glance = Glance_client(
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

    @property
    def flavor(self):
        """Return the flavor for the node."""
        if isinstance(self.host.os_flavor, string_types):
            return self.nova.flavors.find(name=self.host.os_flavor)
        elif isinstance(self.host.os_flavor, int):
            return self.nova.flavors.find(id=str(self.host.os_flavor))

    @flavor.setter
    def flavor(self, value):
        """Raise an exception if flavor is tried to be set."""
        raise ValueError('You cannot set flavor for host after host/'
                         'provisioner have been instantiated.')

    @property
    def image(self):
        """Return the image for the node."""
        return self.nova.glance.find_image(self.host.os_image)

    @image.setter
    def image(self, value):
        """Raise an exception if image is tried to be set."""
        raise ValueError('You cannot set the image for host after host/'
                         'provisioner have been instaniated.')

    @property
    def networks(self):
        """Return the networks for the node."""
        return [self.nova.neutron.find_network(name) for name in
                self.host.os_networks]

    @networks.setter
    def networks(self, value):
        """Raise an exception if networks is tried to be set."""
        raise ValueError('You cannot set the networks for host after host/'
                         'provisioner have been instantiated.')

    def _wait_for(self, label, condition, obj_getter, timeout_sec=120,
                  wait_sec=1):
        """Wait for condition to be true until timeout.

        :param label: used for logging
        :param condition: function that takes the object from obj_getter and
            returns True or False
        :param obj_getter: function that returns the object on which the
            condition is tested
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
                raise OpenstackProvisionerException(label)
            time.sleep(wait_sec)
            obj = obj_getter()
        self.logger.debug('%s - DONE', label)
        return obj

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
        """Wait for node to be deleted and does not exist.

        :param node: Node to teardown
        :return: Node object
        """
        node = self._wait_till_node_not_deleting(node)

        if node is not None:
            raise OpenstackProvisionerException(
                'Unable to delete node %s' % node.name
            )
        return node

    def wait_for_active_state(self, node):
        """Wait for created vm to be active.

        :param: Node to create on openstack
        :returns: Node object
        """
        node = self._wait_till_node_not_building(node)

        if node is None:
            raise OpenstackProvisionerException(
                'Node %s did not become active!' % node.name
            )
        elif node.status != 'ACTIVE' and node.status != 'ERROR':
            self.logger.error('Wrong status %s of node %s', node.status,
                              node.name)
        return node

    def _wait_till_node_not_building(self, node):
        """Wait for node to be done building
        :param node: Node building
        :returns: Node object
        """
        return self._wait_for(
            ('Waiting for %s to finish building..' % node.name),
            lambda node: node.status != 'BUILD',
            lambda: self.get_node_by_id(node.id),
            timeout_sec=120
        )

    def _wait_till_node_not_deleting(self, node):
        """Wait for node to be done deleting.

        :param node: Node being deleted
        :returns: Node object
        """
        return self._wait_for(
            ('Waiting for %s to finish deleting..' % node.name),
            lambda node: node is None,
            lambda: self.get_node_by_name(node.name),
            timeout_sec=300)

    def associate_floating_ip(self, node, max_attempts=MAX_ATTEMPTS):
        """Associate a floating ip to an active node.

        It will attempt to attach a floating ip to the node given within the
        maximum attempts given if errors are found.

        :param node: Node object
        :param max_attempts: Number of tries to attempt to attach float ip
        """
        float_ips = []
        attempt = 1

        self.logger.info('Associate a floating ip to node %s' % node.name)

        while attempt <= max_attempts:
            try:
                # Get floating ip pool network info
                fip_pools = self.neutron.list_networks(
                    name=self.host.os_floating_ip_pool
                )

                for fip_pool in fip_pools['networks']:
                    # Get port info for node given
                    ports = self.neutron.list_ports(device_id=node.id)

                    # Create and add floating ip
                    for port in ports['ports']:
                        float_ips.append(
                            self.neutron.create_floatingip(
                                dict(
                                    floatingip=dict(
                                        floating_network_id=fip_pool['id'],
                                        port_id=port['id']
                                    )
                                )
                            )
                        )
                self.logger.info('Successfully associated floating ip to node '
                                 '%s' % node.name)
                self.logger.debug('Associated floating ips:')
                for fip in float_ips:
                    fip = fip['floatingip']['floating_ip_address']
                    self.logger.debug(' * %s' % fip)
                return float_ips
            except ClientException:
                self.logger.warn('Failed to associate floating ip to node %s'
                                 % node.name)
                wait_time = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('Attempt %s of %s: retrying in %s seconds',
                                 attempt, max_attempts, wait_time)
                time.sleep(wait_time)
                attempt += 1
        else:
            raise OpenstackProvisionerException(
                'Maximum attempts reached to associate a floating ip to node '
                '%s!' % node.name
            )

    def disassociate_floating_ip(self, node, max_attempts=MAX_ATTEMPTS):
        """Disassociate a floating ip from a active node.

        It will attempt to detach a floating ip from the node given within the
        maximum attempts given if errors are found.

        :param node: Node object
        :param max_attempts: Number of tries to attempt to detach float ip
        """
        attempt = 1

        self.logger.info('Disassociate floating ip from node %s' % node.name)

        while attempt <= max_attempts:
            try:
                # Get floating ips for networks
                float_ips_dict = self.neutron.list_floatingips()
                float_ips = [x['floating_ip_address'] for x in
                             float_ips_dict['floatingips']]

                # Get systems ips
                for host_network in self.host.os_networks:
                    # Get systems ips
                    sys_ips_dict = self.nova.servers.ips(node)
                    sys_ips = [x['addr'] for x in sys_ips_dict[host_network]]

                    # Get system floating ips
                    sys_floating_ips = [x for x in sys_ips if x in float_ips]
                    sys_floating_ids = []
                    for x in sys_floating_ips:
                        for y in float_ips_dict['floatingips']:
                            if x == y['floating_ip_address']:
                                sys_floating_ids.append(y['id'])

                    # Disassociate and release floating ip
                    for fip in sys_floating_ids:
                        self.neutron.delete_floatingip(fip)

                    self.logger.info('Successfully disassociated floating ip'
                                     'from node %s' % node.name)
                break
            except ClientException:
                self.logger.warn('Failed to disassociate floating ip from node'
                                 ' %s' % node.name)
                wait_time = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('Attempt %s of %s: retrying in %s seconds',
                                 attempt, max_attempts, wait_time)
                time.sleep(wait_time)
                attempt += 1
        else:
            raise OpenstackProvisionerException(
                'Maximum attempts reached to disassociate a floating ip from '
                'node %s!' % node.name
            )

    def create_node(self, name, image, flavor, nics, keypair,
                    max_attempts=MAX_ATTEMPTS):
        """Create the node (vm).

        It will attempt to create the node given within the maximum attempts
        given if errors are found.

        :param name: Name of vm
        :param image: Image to use to create vm
        :param flavor: Flavor of vm to create
        :param nics: NICS to configure for vm
        :param keypair: Keypair name to be associated with the vm
        :param max_attempts: Number of tries to attempt to create vm
        :returns: Node object"""
        attempt = 1

        self.logger.info('Booting node %s' % name)
        self.logger.debug('Node details:\n'
                          '* keypair=%s\n'
                          '* image=%s\n'
                          '* flavor=%s\n'
                          '* nics=%s' % (keypair, image, flavor, nics))

        while attempt <= max_attempts:
            try:
                node = self.nova.servers.create(
                    name=name,
                    key_name=keypair,
                    image=image,
                    flavor=flavor,
                    nics=nics
                )
                self.logger.info('Successfully booted node %s' % name)
                return node
            except OverLimit:
                self.logger.warn('Quota is not available to create %s',
                                 name)
                wait_time = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('Attempt %s of %s: retrying in %s seconds.',
                                 attempt, max_attempts, wait_time)
                time.sleep(wait_time)
                attempt += 1
        else:
            raise OpenstackProvisionerException(
                'Maximum attempts reached to boot node %s' % name
            )

    def delete_node(self, node, max_attempts=MAX_ATTEMPTS):
        """Delete the node (vm).

        It will attempt to delete the node given within the maximum attempts
        given if errors are found.

        :param node: Node object
        :param max_attempts: Number of tries to attempt to delete vm
        """
        attempt = 1

        self.logger.info('Deleting node %s' % node.name)

        while attempt <= max_attempts:
            try:
                # Request to delete node
                self.nova.servers.delete(node)

                # Wait for node to not exist
                self.wait_for_nonexist_state(node)

                self.logger.info('Successfully deleted node %s' % node.name)
                break
            except (ClientException, OpenstackProvisionerException):
                self.logger.info('Failed to delete node %s' % node.name)
                wait_time = random.randint(10, MAX_WAIT_TIME)
                self.logger.info('Attempt %s of %s: retrying in %s seconds.',
                                 attempt, max_attempts, wait_time)
                time.sleep(wait_time)
                attempt += 1
        else:
            raise OpenstackProvisionerException(
                'Maximum attempts reached to delete node %s' % node.name
            )

    def create(self):
        """Create nodes in openstack. This consists of the following:
            1. Create node.
            2. Assign floating ip to node.
            3. Update carbon.resource.host object with output parameters.

        If any failures occur while node creation, we will call the delete
        method to teardown the resource. This ensures that nodes are not
        left hanging around teams tenants.
        """
        self.logger.info('Provisioning machines from %s', self.__class__)

        try:
            # Create node
            node = self.create_node(
                name=self.host.os_name,
                image=self.image,
                flavor=self.flavor,
                nics=[{'net-id': net.id} for net in self.networks],
                keypair=self.host.os_keypair
            )
        except Exception as ex:
            raise OpenstackProvisionerException(
                'Unable to create node %s. Traceback: %s' %
                (self.host.os_name, ex)
            )

        try:
            # Wait for node to be active
            self.wait_for_active_state(node)
        except OpenstackProvisionerException as ex:
            self.logger.error('%s Deleting node %s.', ex.message, node.name)

            # Delete node
            self.delete_node(node)

            raise OpenstackProvisionerException(ex.message)

        try:
            # Associate floating ip to node
            float_ips = self.associate_floating_ip(node)
        except OpenstackProvisionerException as ex:
            self.logger.error('%s Deleting node %s.', ex.message, node.name)

            # Delete node
            self.delete_node(node)

            raise OpenstackProvisionerException(ex.message)

        # Update host object with node name and node id
        self.host.os_name = str(node.name)
        self.host.os_node_id = str(node.id)

        # Update host object with floating ip addresses
        ips = []
        for ip in float_ips:
            ips.append(str(ip['floatingip']['floating_ip_address']))
        self.host.os_ip_address = ips

        self.logger.info('Successfully created node %s' % self.host.os_name)

    def delete(self):
        """Delete nodes in openstack. This consists of the following:
            1. Check if node to be deleted actually exists.
            2. Delete floating ip from node.
            3. Delete node.
        """
        self.logger.info('Tearing down machines from %s', self.__class__)

        try:
            # Check if the node actually exists
            node = self.get_node_by_name(self.host.os_name)
            if node is None:
                self.logger.warn('Node %s cannot be found! Skipping '
                                 'deletion.' % self.host.os_name)
                return
        except ClientException as ex:
            raise OpenstackProvisionerException(
                'Unable to get node object for %s. Traceback: %s' %
                (self.host.os_name, ex)
            )

        # Disassociate floating ip from node
        self.disassociate_floating_ip(node)

        # Delete node
        self.delete_node(node)
