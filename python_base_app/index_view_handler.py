# -*- coding: utf-8 -*-

# Copyright (C) 2019-2023  Marcus Rickert
#
# See https://github.com/marcus67/python_base_app
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Ideas taken from https://realpython.com/handling-user-authentication-with-angular-and-flask/

import flask
import flask.wrappers
import some_flask_helpers
from flask import make_response
from flask_wtf.csrf import generate_csrf

import python_base_app

INDEX_BLUEPRINT_NAME = 'index'
INDEX_BLUEPRINT_ADAPTER = some_flask_helpers.BlueprintAdapter()

INDEX_REL_URL = '/'
INDEX_ENDPOINT_NAME = "INDEX"


def _(x):
    return x


class IndexViewHandler(object):

    def __init__(self, p_app, p_url_prefix):
        self._app = p_app

        self._url_prefix = p_url_prefix

        self._blueprint = flask.Blueprint(INDEX_BLUEPRINT_NAME, python_base_app.__name__)
        INDEX_BLUEPRINT_ADAPTER.assign_view_handler_instance(p_blueprint=self._blueprint, p_view_handler_instance=self)
        INDEX_BLUEPRINT_ADAPTER.check_view_methods()

        p_app.register_blueprint(self._blueprint, url_prefix=p_url_prefix)

    @INDEX_BLUEPRINT_ADAPTER.route_method(p_rule=INDEX_REL_URL, endpoint=INDEX_ENDPOINT_NAME, methods=["GET"])
    def index(self):
        resp = make_response(f"The Cookie has been set")
        header_name = self._app.config["WTF_CSRF_HEADERS"][0]
        resp.headers[header_name] = generate_csrf()

        return resp

    def destroy(self):
        INDEX_BLUEPRINT_ADAPTER.unassign_view_handler_instances()
