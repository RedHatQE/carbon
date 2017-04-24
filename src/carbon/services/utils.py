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
    carbon.services.utils

    :copyright: (c) 2017 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os

from flask import Flask, json, request, Response
from werkzeug.urls import url_join
from werkzeug.utils import find_modules, import_string

from ..core import CarbonException


class CarbonApiResult(object):
    """
    It helps to store the current value that the API wants
    to generate. It helps to keep API responses consistent
    throughout all the services.
    """
    def __init__(self, value, status=200, next_page=None):
        self.value = value
        self.status = status
        self.next_page = next_page

    def to_response(self):
        """
        It responds with an standard JSON format for all API
        responses. Whenever next_page is set it is added into
        the response header so client can manage the next pages
        for the response.
        :return: JSON response
        """
        rv = Response(json.dumps(self.value),
                        status=self.status,
                        mimetype='application/json')
        if self.next_page is not None:
            rv.headers['Link'] = '<%s>; rel="next"' % \
                url_join(request.url, self.next_page)
        return rv


class CarbonApiService(Flask):
    """
    A wrapper around Flask object so we can keep all Carbon
    services APIs consistent across all different services.
    """
    def make_response(self, rv):
        if isinstance(rv, CarbonApiResult):
            return rv.to_response()
        return Flask.make_response(self, rv)


class CarbonApiException(CarbonException):
    """
    It keeps all Carbon service API exceptions consistent
    responses when something bad happnes.
    """
    def __init__(self, message, status=400):
        self.message = message
        self.status = status

    def to_result(self):
        return CarbonApiResult({'message': self.message},
                               status=self.status)


def register_blueprint(app, package_name):
    """
    It goes through all the modules within the given 'service_module'
    and look for blueprints. If it finds, it register the blueprint
    of that module.
    :param app: the flask app of which the bluenprints will be registered
    :param service_module: the module to which we will look for blueprints
    :return: the flask app with the blueprints registered (if found)
    """
    for name in find_modules(package_name):
        mod = import_string(name)
        if hasattr(mod, 'api_bp'):
            app.register_blueprint(mod.api_bp)


def register_error_handler(app):
    """
    This function lets the flask app knows that when it should use the
    CarbonApiException when an error happens.
    :param app: the flask app to register the error handler
    :return: the app with CarbonApiException registered as an error handler
    """
    app.register_error_handler(
        CarbonApiException, lambda err: err.to_result()
    )


def create_app(config=None, package_name=None):
    """
    This function is a generic application factory to be used by all
    carbon feactories.
    :param config: the flask app configuration
    :param package_name: the package name to get all its blueprints registered
    :return: a flask app
    """
    app = CarbonApiService(__name__)
    app.config.update(config or {})
    if package_name is not None:
        register_blueprint(app, package_name)
    register_error_handler(app)
    return app
