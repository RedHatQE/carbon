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
    carbon.providers.openstack

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from glanceclient.v2.client import Client as glanceclient
from keystoneauth1 import identity, session
from keystoneclient.v2_0.client import Client as keystoneclient
from neutronclient.v2_0.client import Client as neutronclient
from novaclient.client import Client as novaclient
from novaclient.exceptions import ClientException

from ..core import CarbonProvider
from .._compat import string_types


class OpenstackProvider(CarbonProvider):
    """
    Openstack provider implementation.
    The following fields are supported:

        os_flavor: (mandatory) The Flavor to boot onto.

        os_image: (mandatory) The Image to boot with.

        os_nics: (mandatory) An ordered list of nics (dicts) to be
                 added to this server, with information about connected
                 networks, fixed IPs, port etc. his field is required and
                 also supports a single string value of ‘auto’ or ‘none’.
                 The ‘auto’ value means the Compute service will
                 automatically allocate a network for the project if one is
                 not available. The ‘none’ value tells the Compute service
                 to not allocate any networking for the server.

        os_floating_ip_pool: (mandatory) The floating ip pool to use to create
                             a floating IP.

        os_key_name: (optional) name of previously created keypair to
                     inject into the instance

        os_admin_pass: (optional) add a user supplied admin password.

        os_description: (optional) description of the server.

        os_files: (optional) A dict of files to overwrite on the server
                  upon boot. Keys are file names (i.e. /etc/passwd) and
                  values are the file contents (either as a string or as
                  a file-like object). A maximum of five entries is
                  allowed, and each file must be 10k or less.

        os_security_groups: (optional)

        To add more fields for the provider, you have to also create a
        validate_* function for the field. The signature for the function
        must be validate_<paramenter_name> and the return must be True for
        valid or False if the validation fails.

        For instance, the field 'flavor' has the function 'validate_flavor'.

    """
    __provider_name__ = 'openstack'
    __provider_prefix__ = 'os_'

    _mandatory_parameters = (
        'name',
        'flavor',
        'image',
        'networks',
        'floating_ip_pool'
    )

    _optional_parameters = (
        'keypair',
        'admin_pass',
        'description',
        'files',
        'security_groups',
        'node_id',
        'ip_address',
    )

    _output_parameters = (
        'name',
        'node_id',
        'ip_address',
    )

    _mandatory_creds_parameters = (
        'auth_url',
        'tenant_name',
        'tenant_id',
        'username',
        'password',
    )

    _optional_creds_parameters = ()

    def __init__(self, **kwargs):
        super(OpenstackProvider, self).__init__(**kwargs)
        self._nova = None
        self._glance = None
        self._neutron = None

    @property
    def nova(self):
        """Instantiate novaclient (when needed) and return novaclient
        object.
        :return: The novaclient object
        """
        if not self._nova:
            self.nova_connect(self.credentials)
        return self._nova

    @nova.setter
    def nova(self, value):
        """Raises an exception when trying to instantiate the novaclient
        class. Use the nova_connect method to instantiate novaclient.
        :param value: The credentials for Openstack tenant
        """
        raise ValueError('You cannot instantiate novaclient class directly. '
                         'Use method ~OpenstackProvider.nova_connect')

    def nova_connect(self, credentials):
        """Instantiate a novaclient class object.
        :param credentials: The credentials for Openstack tenant
        """
        self._nova = novaclient(
            '2',
            username=credentials['username'],
            password=credentials['password'],
            project_id=credentials['tenant_id'],
            auth_url=credentials['auth_url'],
            project_name=credentials['tenant_name']
        )

    @property
    def glance(self):
        """Instantiate glanceclient (when needed) and return glanceclient
        object.
        :return: The glanceclient object
        """
        if not self._glance:
            self.glance_connect(self.credentials)
        return self._glance

    @glance.setter
    def glance(self, value):
        """Raises an exception when trying to instantiate the glanceclient
        class. Use the glance_connect method to instantiate glanceclient.
        :param value: The credentials for Openstack tenant
        """
        raise ValueError('You cannot instantiate glanceclient class directly.'
                         'Use method ~OpenstackProvider.glance_connect')

    def glance_connect(self, credentials):
        """Instantiate a glanceclient class object.
        :param credentials: The credentials for Openstack tenant
        """
        identity = keystoneclient(
            username=credentials['username'],
            password=credentials['password'],
            tenant_name=credentials['tenant_name'],
            auth_url=credentials['auth_url']
        )
        endpoint = identity.service_catalog.url_for(service_type='image')
        self._glance = glanceclient(endpoint, token=identity.auth_token)

    @property
    def neutron(self):
        """Instantiate neutronclient (when needed) and return neutronclient
        object.
        :return: The neutronclient object
        """
        if not self._neutron:
            self.neutron_connect(self.credentials)
        return self._neutron

    @neutron.setter
    def neutron(self, value):
        """Raises an exception when trying to instantiate the neutronclient
        class. Use the neutron_connect method to instantiate neutronclient.
        :param value: The credentials for Openstack tenant
        """
        raise ValueError('You cannot instantiate neutronclient class directly.'
                         'Use method ~OpenstackProvider.neutron_connect')

    def neutron_connect(self, credentials):
        """Instantiate a neutronclient class object.
        :param credentials: The credentials for Openstack tenant
        """
        auth = identity.Password(
            auth_url=credentials['auth_url'],
            username=credentials['username'],
            password=credentials['password'],
            project_name=credentials['tenant_name']
        )
        sess = session.Session(auth=auth)
        self._neutron = neutronclient(session=sess)

    def validate_name(self, value):
        """Validate the resource name.
        :param value: The resource name
        :return: A boolean, true = valid, false = invalid
        """
        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for name!')
            return False

        # Name must be a string
        if not isinstance(value, string_types):
            self.logger.warn('Name is required to be a string type!')
            return False

        return True

    def validate_flavor(self, value):
        """Validate the resource flavor. The flavor needs to be one of the
        following:
            1. Flavor name ~ m1.medium (string)
            2. Flavor id ~ 3 (integer)
        :param value: The resource flavor
        :return: A boolean, true = valid, false = invalid
        """
        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for flavor!')
            return False

        try:
            if isinstance(value, string_types):
                self.nova.flavors.find(name=value)
            elif isinstance(value, int):
                self.nova.flavors.find(id=str(value))
            else:
                self.logger.warn('Flavor is required to be an integer or '
                                 'string type!')
                return False
        except ClientException as ex:
            self.logger.error(ex)
            return False

        return True

    def validate_image(self, value):
        """Validate the resource image. The image needs to be one of the
        following:
            1. Image name ~ Fedora-Cloud-Base-25-compose-latest (string)
            2. Image id ~ 1e6ff712-b723-4c95-9e18-a393b80d1aff (string)
        :param value: The resource image
        :return: A boolean, true = valid, false = invalid
        """
        _name = None
        _id = None

        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for image!')
            return False

        # Image must be a string
        if not isinstance(value, string_types):
            self.logger.warn('Image is required to be a string type!')
            return False

        for image in self.glance.images.list():
            if str(image.name) == value or str(image.id) == value:
                _name = image.name
                _id = image.id
                break

        if not _name and not _id:
            self.logger.warn('Image %s does not exist!', value)
            return False

        return True

    def validate_networks(self, value):
        """Validate the resource network.
        :param value: The resource network
        :return: A boolean, true = valid, false = invalid
        """
        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for networks!')
            return False

        # Networks must be a list
        if not isinstance(value, list):
            self.logger.warn('Networks is required to be a list type!')
            return False

        try:
            for network in value:
                data = self.neutron.list_networks(name=network)
                if len(data['networks']) <= 0:
                    self.logger.error('Network %s does not exist in tenant!',
                                      network)
                    raise RuntimeError
        except RuntimeError:
            return False

        return True

    def validate_keypair(self, value):
        """Validate the resource keypair.
        :param value: The resource keypair
        :return: A boolean, true = valid, false = invalid
        """
        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for keypair!')
            return False

        # Keypair must be a string
        if not isinstance(value, string_types):
            self.logger.warn('Keypair is required to be a string type!')
            return False

        try:
            self.nova.keypairs.find(name=value)
        except ClientException as ex:
            self.logger.error(ex)
            return False

        return True

    @classmethod
    def validate_admin_pass(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_description(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_files(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    @classmethod
    def validate_security_groups(cls, value):
        if value:
            return isinstance(value, string_types)
        else:
            return True

    def validate_floating_ip_pool(self, value):
        """Validate the resource floating ip pool.
        :param value: The resource floating ip pool
        :return: A boolean, true = valid, false = invalid
        """
        # Quit when no value given
        if not value:
            self.logger.warn('Invalid data for floating ip pool!')
            return False

        # Floating ip pool must be a string
        if not isinstance(value, string_types):
            self.logger.warn('Floating ip pool is required to be a string '
                             'type!')
            return False

        try:
            data = self.neutron.list_networks(name=value)
            if len(data['networks']) <= 0:
                self.logger.error('Floating IP pool: %s does not exist in '
                                  'tenant!' % value)
                raise RuntimeError
        except RuntimeError:
            return False

        return True

    @classmethod
    def validate_node_id(cls, value):
        return True

    @classmethod
    def validate_ip_address(cls, value):
        return True
