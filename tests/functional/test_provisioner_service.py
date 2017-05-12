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
    Set of tests for the provisioner service API

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
try:
    import simplejson as json
except ImportError:
    import json

from carbon.helpers import gen_random_str
from carbon.services.provisioner import app


ERROR_404_MESSAGE = b"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>404 Not Found</title>
<h1>Not Found</h1>
<p>The requested URL was not found on the server.  If you entered the URL manually please check your spelling and try again.</p>
"""


# TODO: This function should grab a job ID from a sample database
def get_valid_job_id():
    """
    Function to assist testing.
    :return:
    """
    return gen_random_str(32)


def get_valid_job_info():
    job_id = gen_random_str(32)
    resource = '/provisioner/jobs/{job_id}'.format(job_id=job_id)
    return resource, job_id


def test_options_get_status():
    rv = app.test_client().open('/provisioner/status', method='OPTIONS')
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS']
    assert rv.data == b''


def test_get_status():
    rv = app.test_client().open('/provisioner/status', method='GET')
    assert json.loads(rv.data) == json.loads('{"get_status": "ok"}')


def test_options_get_jobs():
    rv = app.test_client().open('/provisioner/jobs', method='OPTIONS')
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST']
    assert rv.data == b''


def test_get_jobs():
    rv = app.test_client().open('/provisioner/jobs', method='GET')
    assert json.loads(rv.data) == json.loads('{"get_jobs": "ok"}')


def test_post_jobs():
    rv = app.test_client().open('/provisioner/jobs', method='POST')
    assert json.loads(rv.data) == json.loads('{"post_jobs": "ok"}')


def test_options_get_job():
    rv = app.test_client().open('/provisioner/jobs/1', method='OPTIONS')
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'PUT']
    assert rv.data == b''


def test_get_job():
    for i in range(0, 10):
        uri, job_id = get_valid_job_info()
        rv = app.test_client().open(uri, method='GET')
        response = '{"get_job": "ok", "job_id": "%s"}' % job_id
        assert json.loads(rv.data) == json.loads(response)


def test_put_job():
    for i in range(0, 10):
        uri, job_id = get_valid_job_info()
        rv = app.test_client().open(uri, method='PUT')
        response = '{"put_job": "ok", "job_id": "%s"}' % job_id
        assert json.loads(rv.data) == json.loads(response)


def test_get_job_logs_options():
    rv = app.test_client().open('/provisioner/jobs/1/logs', method='OPTIONS')
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS']
    assert rv.data == b''


def test_get_job_logs():
    for i in range(0, 10):
        uri, job_id = get_valid_job_info()
        rv = app.test_client().open('{uri}/logs'.format(uri=uri),
                                    method='GET')
        response = '{"get_job_logs": "ok", "job_id": "%s"}' % job_id
        assert json.loads(rv.data) == json.loads(response)


def test_post_job_teardown_options():
    rv = app.test_client().open('/provisioner/jobs/1/teardown', method='OPTIONS')
    assert sorted(rv.allow) == ['OPTIONS', 'POST']
    assert rv.data == b''


def test_post_jobs_teardown():
    for i in range(0, 10):
        uri, job_id = get_valid_job_info()
        rv = app.test_client().open('{uri}/teardown'.format(uri=uri),
                                    method='POST')
        response = '{"post_job_teardown": "ok", "job_id": "%s"}' % job_id
        assert json.loads(rv.data) == json.loads(response)


def test_get_job_nodes_options():
    rv = app.test_client().open('/provisioner/jobs/1/nodes', method='OPTIONS')
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS']
    assert rv.data == b''


def test_get_job_nodes():
    for i in range(0, 10):
        uri, job_id = get_valid_job_info()
        rv = app.test_client().open('{uri}/nodes'.format(uri=uri),
                                    method='GET')
        response = '{"get_job_nodes": "ok", "job_id": "%s"}' % job_id
        assert json.loads(rv.data) == json.loads(response)


def test_get_job_node_logs():
    for i in range(0, 10):
        uri, job_id = get_valid_job_info()
        rv = app.test_client().open('{uri}/nodes/aaa/logs'.format(uri=uri),
                                    method='GET')
        response = ('{"get_job_node_logs": "ok",'
                    '"job_id": "%s", "node_id": "aaa"}' % job_id)
        assert json.loads(rv.data) == json.loads(response)


def test_post_job_node_teardown_options():
    rv = app.test_client().open('/provisioner/jobs/1/nodes/1/teardown',
                                method='OPTIONS')
    assert sorted(rv.allow) == ['OPTIONS', 'POST']
    assert rv.data == b''


def test_post_job_node_teardown():
    for i in range(0, 10):
        uri, job_id = get_valid_job_info()
        rv = app.test_client().open('{uri}/nodes/aaa/teardown'
                                    .format(uri=uri), method='POST')
        response = ('{"post_job_node_teardown": "ok",'
                    '"job_id": "%s", "node_id": "aaa"}' % job_id)
        assert json.loads(rv.data) == json.loads(response)


def test_404_message():
    rv = app.test_client().open('/provisioner/blabla', method='GET')
    assert rv.data == ERROR_404_MESSAGE
