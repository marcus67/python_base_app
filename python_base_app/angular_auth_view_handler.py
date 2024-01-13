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
#
# Ideas taken from https://realpython.com/handling-user-authentication-with-angular-and-flask/

import datetime
from json import JSONDecodeError

import flask
import flask.wrappers
import some_flask_helpers
from flask import jsonify, request

import python_base_app
from python_base_app.base_token_handler import BaseTokenHandler, TokenException
from python_base_app.base_user_handler import BaseUserHandler

ANGULAR_AUTH_BLUEPRINT_NAME = 'angular_auth'
ANGULAR_AUTH_BLUEPRINT_ADAPTER = some_flask_helpers.BlueprintAdapter()

ANGULAR_LOGIN_ENDPOINT_NAME = "angular-login"
ANGULAR_LOGOUT_ENDPOINT_NAME = "angular-logout"
ANGULAR_STATUS_ENDPOINT_NAME = "angular-status"

ANGULAR_BASE_URL = '/angular-api'
ANGULAR_LOGIN_REL_URL = '/login'
ANGULAR_LOGOUT_REL_URL = '/logout'
ANGULAR_STATUS_REL_URL = '/status'


def _(x):
    return x


# for pybabel:
_('Please log in to access this page.')


class AngularAuthViewHandler(object):

    def __init__(self, p_user_handler: BaseUserHandler, p_app, p_url_prefix: str, p_token_handler: BaseTokenHandler):

        self._user_handler = p_user_handler
        self._token_handler = p_token_handler
        self._url_prefix = p_url_prefix

        self._blueprint = flask.Blueprint(ANGULAR_AUTH_BLUEPRINT_NAME, python_base_app.__name__)
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.assign_view_handler_instance(p_blueprint=self._blueprint,
                                                                    p_view_handler_instance=self)
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.check_view_methods()

        p_app.register_blueprint(self._blueprint, url_prefix=p_url_prefix)

    def check_user(self, p_username, p_password):

        return self._user_handler.authenticate(p_username=p_username, p_password=p_password)

    def check_authorization(self, p_request):

        http_status = 200
        error_details = None
        result = {
            'status': "OK",
        }

        # get the auth token
        auth_header = p_request.headers.get('Authorization')

        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]

                if auth_token is not None:
                    username = self._token_handler.decode_auth_token(p_token=auth_token)
                    uid = self._user_handler.get_uid(username)

                    if uid is not None:
                        result['authorization'] = {
                            'uid': uid,
                            'username': username,
                        }
                    else:
                        http_status = 401
                        error_details = f"username '{username} not found found"

                else:
                    http_status = 401
                    error_details = 'auth token not valid'

            except TokenException as e:
                http_status = 401
                error_details = str(e)

            except IndexError:
                http_status = 401
                error_details = 'bearer token malformed'
        else:
            http_status = 401
            error_details = 'bearer token missing'

        if error_details is not None:
            result['status'] = 'ERROR'
            result['error_details'] = error_details

        return result, http_status


    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_LOGIN_REL_URL,
                                                 endpoint=ANGULAR_LOGIN_ENDPOINT_NAME,
                                                 methods=["POST"])
    def login(self):

        status = "OK"
        auth_token: str = "NOT SET"
        error_details = None
        a_request = flask.globals.request
        http_status = 200

        try:
            if not a_request.is_json:
                error_details = "No JSON found (wrong content type?)"
                http_status = 400

            else:
                payload = a_request.json

                username = payload['username']
                password = payload['password']

                login_valid = self.check_user(p_username=username, p_password=password)

                if login_valid:
                    auth_token = self._token_handler.create_token(p_id=username)

                else:
                    error_details = f"User '{username}' not found or wrong password"
                    http_status = 401

        except (JSONDecodeError, TypeError) as e:
            error_details = f"Invalid JSON: {str(e)}"
            http_status = 400

        except KeyError as e:
            error_details = f"Parameter missing: {str(e)}"
            http_status = 400

        except Exception as e:
            error_details = f"Exception during login: {str(e)}"
            http_status = 400

        result = {
            'status': status,
        }

        if error_details is None:
            result['auth_token'] = auth_token

        else:
            result['status'] = "ERROR"
            result['error_details'] = error_details

        return jsonify(result), http_status

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_STATUS_REL_URL,
                                                 endpoint=ANGULAR_STATUS_ENDPOINT_NAME,
                                                 methods=["GET"])
    def status(self):

        result, http_status = self.check_authorization(p_request=request)
        return jsonify(result), http_status

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_LOGOUT_REL_URL, endpoint=ANGULAR_LOGOUT_ENDPOINT_NAME,
                                                 methods=["POST"])
    def logout(self):

        http_status = 200
        error_details = None
        result = {
            'status': "OK",
        }

        auth_header = request.headers.get('Authorization')

        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''

        try:
            if auth_token:
                self._token_handler.decode_auth_token(auth_token)
                self._token_handler.delete_token(p_token=auth_token, p_deletion_time=datetime.datetime.utcnow())
                result['message'] = 'Successfully logged out.'

            else:
                http_status = 403
                error_details = "auth token is invalid"

        except Exception as e:
            http_status = 403
            error_details = str(e)

        if error_details is not None:
            result['status'] = "ERROR"
            result['error_details'] = error_details

        return jsonify(result), http_status

    def destroy(self):
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.unassign_view_handler_instances()
