# -*- coding: utf-8 -*-
import json
from json import JSONDecodeError

import flask
import flask.wrappers
import flask_login
import some_flask_helpers
from flask import jsonify

import python_base_app

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

ANGULAR_AUTH_BLUEPRINT_NAME = 'angular_auth'
ANGULAR_AUTH_BLUEPRINT_ADAPTER = some_flask_helpers.BlueprintAdapter()

ANGULAR_LOGIN_ENDPOINT_NAME = "angular-login"
ANGULAR_LOGOUT_ENDPOINT_NAME = "angular-logout"

ANGULAR_LOGIN_REL_URL = '/angular-api/login'


def _(x):
    return x


# for pybabel:
_('Please log in to access this page.')


class User(flask_login.UserMixin):

    def __init__(self, p_username):
        self.username = p_username
        self.id = p_username

    def get_id(self):
        return self.id


class AngularAuthViewHandler(object):

    def __init__(self, p_user_handler, p_app, p_url_prefix,
                 p_logged_out_endpoint=ANGULAR_LOGIN_ENDPOINT_NAME):

        self._user_handler = p_user_handler
        self._logged_out_endpoint = p_logged_out_endpoint
        self._url_prefix = p_url_prefix

        self._login_manager = flask_login.LoginManager()
        self._login_manager.init_app(app=p_app)
        self._login_manager.login_view = ANGULAR_AUTH_BLUEPRINT_NAME + '.' + ANGULAR_LOGIN_ENDPOINT_NAME
        self._login_manager.user_loader(self.load_user)

        # See https://flask-login.readthedocs.io/en/latest/#how-it-works
        self._login_manager.session_protection = "strong"

        self._blueprint = flask.Blueprint(ANGULAR_AUTH_BLUEPRINT_NAME, python_base_app.__name__)
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.assign_view_handler_instance(p_blueprint=self._blueprint,
                                                                    p_view_handler_instance=self)
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.check_view_methods()

        p_app.register_blueprint(self._blueprint, url_prefix=p_url_prefix)

    def load_user(self, p_user_id):

        if self._user_handler.is_admin(p_user_id):
            return User(p_username=p_user_id)

        else:
            return None

    def check_user(self, p_username, p_password):

        if self._user_handler.authenticate(p_username=p_username, p_password=p_password):
            return User(p_username=p_username)

        else:
            return None

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_LOGIN_REL_URL, endpoint=ANGULAR_LOGIN_ENDPOINT_NAME,
                                                 methods=["POST"])
    def login(self):

        auth_status: bool = False
        error = None
        error_details = None
        request = flask.globals.request
        http_status = 200

        try:
            payload = json.loads(request.json)

            username = payload['username']
            password = payload['password']

            user = self.check_user(p_username=username, p_password=password)

            if user is not None:
                flask_login.login_user(user)
                auth_status = True

        except JSONDecodeError as e:
            error = "Invalid JSON"
            error_details = str(e)

        except KeyError as e:
            error = "Parameter missing"
            error_details = str(e)

        result = {'result': auth_status}

        if error is not None:
            result['error'] = error
            result['error_details'] = error_details
            http_status = 400

        return jsonify(result), http_status

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule='/logout', endpoint=ANGULAR_LOGOUT_ENDPOINT_NAME,
                                                 methods=["POST"])
    def logout(self):

        flask_login.logout_user()
        return flask.redirect(flask.url_for(self._logged_out_endpoint))

    def destroy(self):
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.unassign_view_handler_instances()
