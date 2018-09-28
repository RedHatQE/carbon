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
    carbon.provisioners.ext.blueprint

    An example provisioner module to be used as a base for implementing any
    new provisioners within carbon.

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from pprint import pformat

from carbon.core import CarbonProvisioner


class BluePrintProvisioner(CarbonProvisioner):
    """Blueprint provisioner class.

    This class demonstrates how you can add a new provisioner into carbon.

    Steps:
      1. First lets copy this module into carbon.provisioners and rename it.
        - i.e. cp blueprint.py ../customprovisioner123.py
      2. Open the module to change the following to reflect the provisioner:
        - Change the name of the class
            - i.e BluePrintProvisioner -> CustomProvisioner123
        - Change the attribute __provisioner_name__
            - i.e __provisioner_name__ = 'blueprint' -> 'customprovisioner123'
        - Open the provisioners package __init__ module and add a new import
          for this class.
            - i.e. from .customprovisioner123 import CustomProvisioner123

    Once you have completed those steps, you will want to update your host
    resource defined in your scenario descriptor file to point to this
    provisioner.

    i.e.
        ---
        provision:
          - name: node01
            role: client
            provider:
              name: openstack
              image: image
              flavor: flavor
              network:
                - network
              floating_ip_pool: 0.0.0.0
              keypair: keypair
            provisioner: customprovisioner123

    Without properly setting the provisioner key, carbon may not call the
    correct provisioner you want to use.
    """
    __provisioner_name__ = 'blueprint'

    def __init__(self, host):
        """Constructor.

        Each host resource is linked to a provider which is the location where
        the host will be provisioned. Along with the provider you will also
        have access to all the provider parameters needed to fulfill the
        provision request. (i.e. images, flavor, network, etc. depending on
        the provider).

        Common Attributes:
          - name: data_folder
            description: the runtime folder where all files/results are stored
            and archived for historical purposes.
            type: string

          - name: provider
            description: name of the provider where host is to be created or
            deleted.
            type: string

          - name: provider_params
            description: available data about the host to be created or
            deleted in the provider defined.
            type: dictionary

          - name: provider_credentials
            description: credentials for the provider associated to the host
            resource.
            type: dictionary

          - name: workspace
            description: workspace where carbon can access all files needed
            by the scenario in order to successfully run it.
            type: string

        There can be more information within the host resource but the ones
        defined above are the most commonly ones used by provisioners.

        :param host: carbon host resource
        :type host: object
        """
        super(BluePrintProvisioner, self).__init__(host)

    def print_commonly_used_attributes(self):
        """Print commonly used attributes from the class instance."""
        self.logger.info('Available provider parameters:\n %s' %
                         pformat(self.provider_params))
        self.logger.info('Available provider credentials:\n %s' %
                         pformat(self.provider_credentials))

    def create(self):
        """Create method. (must implement!)

        Provision the host supplied.
        """
        host = getattr(self.host, 'name')
        self.logger.info('Provisioning host %s in %s.' % (host, self.provider))

        self.print_commonly_used_attributes()

        # (mock) woo hoo! machine is up and accessible by the network
        # lets add the ip address to the host resource for later use by carbon
        setattr(self.host, 'ip_address', '0.0.0.0')

        self.logger.info('Successfully provisioned host %s.' % host)

    def delete(self):
        """Delete method. (must implement!)

        Teardown the host supplied.
        """
        host = getattr(self.host, 'name')
        self.logger.info('Delete host %s in %s.' % (host, self.provider))
        self.print_commonly_used_attributes()
        self.logger.info('Successfully deleted host %s.' % host)
