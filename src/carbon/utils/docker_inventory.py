#!/usr/bin/env python

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
    carbon.utils.docker_inventory

    An Ansible dynamic inventory script for docker containers. To use this
    script you will need to have docker engine running on your system. You
    also need to have the following python package installed:

    - docker>=2.1.0

    You can run the script to return a list of all containers on your system:

    - ./docker_inventory.py --list

    Or you can return a specific container that you define:

    - ./docker_inventory.py --host my_container

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""

from argparse import ArgumentParser
from copy import deepcopy
from json import dumps

from docker import DockerClient


class DockerInventory(object):
    """Docker inventory class.

    This class will generate the data structure needed by ansible inventory
    host for either all containers on your system or the one you declare. The
    data structure generated is in JSON format.

    Sample output:
    {
        "all": {
            "hosts": ["1234"]
        },
        "_meta": {
            "hostvars": {
                "1234": {"ansible_connection": "docker"}
            }
        }
    }
    """

    _data_structure = {'all': {'hosts': []}, '_meta': {'hostvars': {}}}

    def __init__(self, option):
        """Constructor.

        When the docker inventory class is instanticated, it performs the
        following tasks:
            * Instantiate the docker client class to create a docker object.
            * Generate the JSON data structure.
            * Print the JSON data structure for ansible to use.
        """
        self.docker = DockerClient()

        if option.list:
            data = self.containers()
        elif option.host:
            data = self.containers_by_host(option.host)
        else:
            data = self._data_structure
        print(dumps(data))

    def get_containers(self):
        """Return all docker containers on the system.

        :return: Collection of containers.
        """
        return self.docker.containers.list(all=True)

    def containers(self):
        """Return all docker containers to be used by ansible inventory host.

        :return: Ansible required JSON data structure with containers.
        """
        resdata = deepcopy(self._data_structure)
        for container in self.get_containers():
            resdata['all']['hosts'].append(container.name)
            resdata['_meta']['hostvars'][container.name] = \
                {'ansible_connection': 'docker'}

        return resdata

    def containers_by_host(self, host=None):
        """Return the docker container requested to be used by ansible
        inventory host.

        :param host: Host name to search for.
        :return: Ansible required JSON data structure with containers.
        """
        resdata = deepcopy(self._data_structure)
        for container in self.get_containers():
            if str(container.name) == host:
                resdata['all']['hosts'].append(container.name)
                resdata['_meta']['hostvars'][container.name] = \
                    {'ansible_connection': 'docker'}
                break

        return resdata


if __name__ == "__main__":
    PARSER = ArgumentParser()
    PARSER.add_argument('--list', action='store_true')
    PARSER.add_argument('--host')

    DockerInventory(PARSER.parse_args())
