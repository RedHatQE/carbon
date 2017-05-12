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
    carbon.services.apis.provisioner

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os

import requests
from requests.compat import urljoin

from ... import __version__ as carbon_version
from .version import __version__ as api_version
from ...core import CarbonException


__all__ = [
    'ProvisionerApi'
]


# TODO: move the global vars into Carbon config object.
API_HOST = 'http://pit-carbon-stage.rhev-ci-vms.eng.rdu2.redhat.com/provisioner/'


class Response(object):
    """The response from an client call"""
    def __init__(self, req_response):
        """
        :param req_response: the return value from a request
                             call (i.e requests.get)
        :type req_response: requests response object
        """
        self._headers = req_response.headers
        self._content = req_response.content
        self._status_code = req_response.status_code
        self._json = req_response.json

    @property
    def status_code(self):
        """
        :return: integer status code from the call
        """
        return self._status_code

    @property
    def content(self):
        """
        :return: string of the response body
        """
        return self._content

    @property
    def headers(self):
        """
        :return: string of the response header
        """
        return self._headers

    @property
    def json(self):
        """
        :return: the json response
        """
        return self._json


# TODO: create a carbon client object
# TODO: generalize the API class object to the carbon client object
# TODO: Add authentication to the api class
class ProvisionerApi(object):
    """
    Main API class for the provisioner.
    """
    def __init__(self, **opts):
        """
        Construct Provisioner API object

        :param host: base URL for the provisioner service
        :type host: string
        :param apikey: the api key used for service authentiation
        :type host: string
        """
        self._host = opts.get('host', API_HOST)
        self._apikey = opts.get('apikey', os.environ.get('CBN_PROV_API_KEY'))
        self._useragent = 'CBNProvisionerAPI/c{0}-a{1}'.format(carbon_version,
                                                               api_version)

        self._headers = {
            "Authorization": 'Carbon {0}'.format(self._apikey),
            "User-agent": self._useragent,
            "Accept": 'application/json'
        }

    def _get(self, url, data=None):
        try:
            r = requests.get(url, headers=self._headers, data=data)
        except CarbonException as ex:
            raise ex
        return r

    def _put(self, url, data=None):
        try:
            r = requests.put(url, headers=self._headers, data=data)
        except CarbonException as ex:
            raise ex
        return r

    def _post(self, url, data=None):
        try:
            r = requests.post(url, headers=self._headers, data=data)
        except CarbonException as ex:
            raise ex
        return r

    def _get_status(self):
        resource = 'status'
        url = urljoin(self._host, resource)
        r = self._get(url)
        return r

    def status(self):
        """
        Get the status of the provisioner service and its version
        if the service is up and running
        :return: informative parameters about the service
        """
        return self._get_status()

    def _get_jobs(self):
        """
        Invoke the API interface to get the list of jobs for the
        current user.
        :return: list of jobs in a dictionary
        """
        resource = 'jobs'
        url = urljoin(self._host, resource)
        r = self._get(url)
        return r

    def get_jobs(self):
        """
        Get the latest 100 jobs for the current user
        :return: list of jobs in a dictionary
        """
        return self._get_jobs()

    def _post_jobs(self, data):
        """
        Invoke the POST jobs to create a new job.
        :param data: parameters for the job to be created
        :return: return the API response
        """
        resource = 'jobs'
        url = urljoin(self._host, resource)
        r = self._post(url, data=data)
        return r

    def create_job(self, data):
        """
        Create a new job
        :param data: job parameters
        :return: job id
        """
        return self._post_jobs(data)

    def _get_job(self, job_id):
        resource = 'jobs/{job_id}'.format(job_id=job_id)
        url = urljoin(self._host, resource)
        r = self._get(url)
        return r

    def get_job(self, job_id):
        """
        :param job_id: the job id to be looked up
        :type job_id: string
        :return:
        """
        return self._get_job(job_id)

    def _put_job(self, job_id, data):
        """
        Change job parameters

        :param job_id: id of the job that is about to be changed
        :type job_id: string
        :param data: job parameters to be changed.
        :type data: dictionary
        :return: API response for the change request
        """
        resource = 'jobs/{job_id}'.format(job_id=job_id)
        url = urljoin(self._host, resource)
        r = self._put(url, data)
        return r

    def update_job(self, job_id, data):
        """
        :param job_id: the job id that is about to be changed
        :param data: the parameters that will be replaced
        :return: API response
        """
        return self._put_job(job_id, data)

    def _get_job_logs(self, job_id):
        resource = 'jobs/{job_id}/logs'.format(job_id=job_id)
        url = urljoin(self._host, resource)
        r = self._get(url)
        return r

    def get_job_logs(self, job_id):
        """
        :param job_id:
        :return: API response
        """
        return self._get_job_logs(job_id)

    def _post_job_teardown(self, job_id):
        resource = 'jobs/{job_id}/teardown'.format(job_id=job_id)
        url = urljoin(self._host, resource)
        r = self._post(url)
        return r

    def teardown_job(self, job_id):
        """
        Teardown all nodes of the specified job.
        :param job_id: the job id
        :return: API response
        """
        return self._post_job_teardown(job_id)

    def _get_job_nodes(self, job_id):
        resource = 'jobs/{job_id}/nodes'.format(job_id=job_id)
        url = urljoin(self._host, resource)
        r = self._get(url)
        return r

    def get_job_nodes(self, job_id):
        """
        :param job_id:
        :return: API response
        """
        return self._get_job_nodes(job_id)

    def _post_node_teardown(self, job_id, node_id):
        resource = 'jobs/{job_id}/nodes/{node_id}/teardown' \
            .format(job_id=job_id, node_id=node_id)
        print(resource)
        url = urljoin(self._host, resource)
        print(url)
        r = self._post(url)
        return r

    def teardown_node(self, job_id, node_id):
        return self._post_node_teardown(job_id, node_id)

    def _get_node_logs(self, job_id, node_id):
        resource = 'jobs/{job_id}/nodes/{node_id}/logs'\
            .format(job_id=job_id, node_id=node_id)
        url = urljoin(self._host, resource)
        r = self._get(url)
        return r

    def get_node_logs(self, job_id, node_id):
        return self._get_node_logs(job_id, node_id)
