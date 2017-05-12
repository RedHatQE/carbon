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
    Set of tests for the provisioner client API library

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import time
import multiprocessing as mp

try:
    import simplejson as json
except ImportError:
    import json

from carbon.services.provisioner import app
from carbon.services.apis import ProvisionerApi
from carbon.helpers import gen_random_str


class TestProvisionerApi(object):

    @classmethod
    def setUpClass(cls):
        cls.hostname = 'http://localhost:7000/provisioner/'
        with app.app_context():
            cls.p = mp.Process(target=app.run, kwargs={'port': 7000})
            cls.p.start()
            time.sleep(2)

    def setUp(self):
        self.api = ProvisionerApi(host=self.hostname)

    @classmethod
    def get_valid_job_id(cls):
        """
        Function to assist testing.
        :return:
        """
        return gen_random_str(32)

    def test_get_status(self):
        rv = self.api.status()
        assert json.loads(rv.content) == json.loads('{"get_status": "ok"}')

    def test_get_jobs(self):
        rv = self.api.get_jobs()
        assert json.loads(rv.content) == json.loads('{"get_jobs": "ok"}')

    def test_create_job(self):
        data = '{"data": "some_data"}'
        rv = self.api.create_job(data)
        assert json.loads(rv.content) == json.loads('{"post_jobs": "ok"}')

    def test_get_job(self):
        for i in range(0, 10):
            job_id = self.get_valid_job_id()
            rv = self.api.get_job(job_id)
            response = '{"get_job": "ok", "job_id": "%s"}' % job_id
            assert json.loads(rv.content) == json.loads(response)

    def test_update_job(self):
        data = '{"data": "some_data"}'
        for i in range(0, 10):
            job_id = self.get_valid_job_id()
            rv = self.api.update_job(job_id, data)
            response = '{"put_job": "ok", "job_id": "%s"}' % job_id
            assert json.loads(rv.content) == json.loads(response)

    def test_get_job_logs(self):
        for i in range(0, 10):
            job_id = self.get_valid_job_id()
            rv = self.api.get_job_logs(job_id)
            response = '{"get_job_logs": "ok", "job_id": "%s"}' % job_id
            assert json.loads(rv.content) == json.loads(response)

    def test_teardown_job(self):
        job_id = self.get_valid_job_id()
        rv = self.api.teardown_job(job_id)
        response = '{"post_job_teardown": "ok", "job_id": "%s"}' % job_id
        assert json.loads(rv.content) == json.loads(response)

    def test_get_job_nodes(self):
        job_id = self.get_valid_job_id()
        rv = self.api.get_job_nodes(job_id)
        response = '{"get_job_nodes": "ok", "job_id": "%s"}' % job_id
        assert json.loads(rv.content) == json.loads(response)

    def test_teardown_node(self):
        job_id = self.get_valid_job_id()
        node_id = "aaa"
        rv = self.api.teardown_node(job_id, node_id)
        response = '{"post_job_node_teardown": "ok", "job_id": "%s", "node_id": "aaa"}' % job_id
        print(rv.content)
        assert json.loads(rv.content) == json.loads(response)

    def test_get_node_logs(self):
        job_id = self.get_valid_job_id()
        node_id = "aaa"
        rv = self.api.get_node_logs(job_id, node_id)
        response = '{"get_job_node_logs": "ok", "job_id": "%s", "node_id": "aaa"}' % job_id
        print(rv.content)
        assert json.loads(rv.content) == json.loads(response)

    @classmethod
    def tearDownClass(cls):
        cls.p.terminate()
