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
    carbon.services.provisioner.views

    Here you add brief description of what this module is about

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
from flask import Blueprint

from ..utils import CarbonApiResult


api_bp = Blueprint('api', __name__, url_prefix='/provisioner')


@api_bp.route('/status')
def get_status():
    return CarbonApiResult({'get_status': 'ok'})


@api_bp.route('/jobs', methods=['GET'])
def get_jobs():
    return CarbonApiResult({'get_jobs': 'ok'})


@api_bp.route('/jobs', methods=['POST'])
def post_jobs():
    return CarbonApiResult({'post_jobs': 'ok'})


@api_bp.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    return CarbonApiResult({'get_job': 'ok',
                            'job_id': job_id})


@api_bp.route('/jobs/<int:job_id>', methods=['PUT'])
def put_job(job_id):
    return CarbonApiResult({'put_job': 'ok',
                            'job_id': job_id})


@api_bp.route('/jobs/<int:job_id>/logs', methods=['GET'])
def get_job_logs(job_id):
    return CarbonApiResult({'get_job_logs': 'ok',
                            'job_id': job_id})


@api_bp.route('/jobs/<int:job_id>/teardown', methods=['POST'])
def post_job_teardown(job_id):
    return CarbonApiResult({'post_job_terdown': 'ok',
                            'job_id': job_id})


@api_bp.route('/jobs/<int:job_id>/nodes/<int:node_id>/teardown', methods=['POST'])
def post_job_node_teardown(job_id, node_id):
    return CarbonApiResult({'post_job_node_teardown': 'ok',
                            'job_id': job_id,
                            'node_id': node_id})


@api_bp.route('/jobs/<int:job_id>/nodes/<int:node_id>/logs', methods=['GET'])
def get_job_node_logs(job_id, node_id):
    return CarbonApiResult({'get_job_node_logs': 'ok',
                            'job_id': job_id,
                            'node_id': node_id})
