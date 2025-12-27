# -*- coding: utf-8 -*-
# Copyright (C) 2019-2025  Marcus Rickert
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
from typing import Callable

import flask
import flask.wrappers
import some_flask_helpers
from flask import jsonify, request, make_response, Request

import python_base_app
from python_base_app import log_handling
from python_base_app.base_token_handler import BaseTokenHandler, TokenException
from python_base_app.base_user_handler import BaseUserHandler

ANGULAR_AUTH_BLUEPRINT_NAME = 'angular_auth'
ANGULAR_AUTH_BLUEPRINT_ADAPTER = some_flask_helpers.BlueprintAdapter()

ANGULAR_LOGIN_ENDPOINT_NAME = "angular-login"
ANGULAR_LOGOUT_ENDPOINT_NAME = "angular-logout"
ANGULAR_STATUS_ENDPOINT_NAME = "angular-status"
ANGULAR_REFRESH_ENDPOINT_NAME = "angular-refresh"

ANGULAR_BASE_URL = '/angular-api'
ANGULAR_LOGIN_REL_URL = '/login'
ANGULAR_LOGOUT_REL_URL = '/logout'
ANGULAR_STATUS_REL_URL = '/login-status'
ANGULAR_REFRESH_REL_URL = '/refresh'

AUTH_COOKIE_NAME = "authCookie"
REFRESH_COOKIE_NAME = "refreshCookie"


def _(x):
    return x


# for pybabel:
_('Please log in to access this page.')


class AngularAuthViewHandler:

    def __init__(self, p_user_handler: BaseUserHandler, p_app, p_url_prefix: str,
                 p_token_handler: BaseTokenHandler,
                 p_auth_result_processor:Callable[[dict], int|None] = None):

        self._user_handler = p_user_handler
        self._token_handler = p_token_handler
        self._url_prefix = p_url_prefix
        self._auth_result_processor:Callable[[dict], int|None] = p_auth_result_processor

        self._logger = log_handling.get_logger(self.__class__.__name__)

        self._blueprint = flask.Blueprint(ANGULAR_AUTH_BLUEPRINT_NAME, python_base_app.__name__)
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.assign_view_handler_instance(p_blueprint=self._blueprint,
                                                                    p_view_handler_instance=self)
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.check_view_methods()

        p_app.register_blueprint(self._blueprint, url_prefix=p_url_prefix)

    @property
    def blueprint(self):
        return self._blueprint

    def check_user(self, p_username, p_password):

        return self._user_handler.authenticate(p_username=p_username, p_password=p_password)

    def check_authorization(self, p_request: Request, p_admin_required: bool = True) -> tuple[any, int]:

        http_status = 200
        error_details = None
        result = {
            'status': "OK",
        }

        # get the auth token
        auth_cookie = p_request.cookies.get(AUTH_COOKIE_NAME)

        if auth_cookie:
            try:
                username = self._token_handler.decode_auth_token(p_token=auth_cookie, p_is_refresh=False)
                uid = self._user_handler.get_uid(username)

                if uid is not None:
                    is_admin = self._user_handler.is_admin(username)

                    if is_admin or not p_admin_required:
                        result['authorization'] = {
                            'uid': uid,
                            'username': username,
                            'is_admin': is_admin
                        }

                        if self._auth_result_processor:
                            self._auth_result_processor(result['authorization'])
                    else:
                        http_status = 401
                        error_details = f"username '{username}' is not in admin group"
                else:
                    http_status = 401
                    error_details = f"username '{username}' not found"

            except TokenException as e:
                http_status = 401
                error_details = str(e)

        else:
            http_status = 401
            error_details = 'auth cookie missing'

        if error_details is not None:
            result['status'] = 'ERROR'
            result['error_details'] = error_details
            self._logger.warn(error_details)

        return result, http_status

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_LOGIN_REL_URL,
                                                 endpoint=ANGULAR_LOGIN_ENDPOINT_NAME,
                                                 methods=["POST"])
    def login(self):

        result = {}
        auth_token: str | None = None
        refresh_token: str | None = None
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
                    is_admin = self._user_handler.is_admin(username)
                    result["is_admin"] = is_admin
                    result["username"] = username
                    auth_token = self._token_handler.create_token(p_id=username)
                    refresh_token = self._token_handler.create_token(p_id=username, p_is_refresh=True)

                    if self._auth_result_processor:
                        self._auth_result_processor(result)

                    self._logger.info(f"User {username} logged in successfully.")

                else:
                    error_details = f"User '{username}' not found or wrong password"
                    self._logger.warn(error_details)
                    http_status = 401

        except (JSONDecodeError, TypeError) as e:
            error_details = f"Invalid JSON: {e!s}"
            http_status = 400

        except KeyError as e:
            error_details = f"Parameter missing: {e!s}"
            http_status = 400

        except Exception as e:
            error_details = f"General exception during login: {e!s}"
            http_status = 400

        if error_details is None:
            result['status'] = "OK"

        else:
            result['status'] = "ERROR"
            result['error_details'] = error_details

        response = make_response(jsonify(result), http_status)

        if auth_token is not None:
            response.set_cookie(key=AUTH_COOKIE_NAME, value=auth_token, httponly=True)

        if refresh_token is not None:
            response.set_cookie(key=REFRESH_COOKIE_NAME, value=refresh_token, httponly=True)

        return response

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_REFRESH_REL_URL,
                                                 endpoint=ANGULAR_REFRESH_ENDPOINT_NAME,
                                                 methods=["POST"])
    def refresh(self):

        status = "OK"
        access_token: str = "NOT SET"
        error_details = None
        username: str = "NOT SET"
        http_status = 200

        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

        if not refresh_token:
            error_details = "No refresh cookie found"
            http_status = 400

        else:
            try:
                username = self._token_handler.decode_auth_token(refresh_token, p_is_refresh=True)
                access_token = self._token_handler.create_token(p_id=username, p_is_refresh=False)

            except TokenException as e:
                error_details = f"Exception '{e!s}' while checking refresh token!"
                http_status = 400

        result = {
            'status': status,
        }

        if error_details is None:
            result['status'] = "OK"
            self._logger.debug(f"Refreshed access token for user '{username}'.")

        else:
            result['status'] = "ERROR"
            result['error_details'] = error_details

        response = make_response(jsonify(result), http_status)

        if access_token is not None:
            response.set_cookie(key=AUTH_COOKIE_NAME, value=access_token, httponly=True)

        return response

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_STATUS_REL_URL,
                                                 endpoint=ANGULAR_STATUS_ENDPOINT_NAME,
                                                 methods=["GET"])
    def status(self):

        result, http_status = self.check_authorization(p_request=request, p_admin_required=False)
        return jsonify(result), http_status

    @ANGULAR_AUTH_BLUEPRINT_ADAPTER.route_method(p_rule=ANGULAR_LOGOUT_REL_URL, endpoint=ANGULAR_LOGOUT_ENDPOINT_NAME,
                                                 methods=["POST"])
    def logout(self):

        error_details: str | None = None
        result = {}

        try:
            result, http_status = self.check_authorization(p_request=request, p_admin_required=False)

            if http_status == 200:
                auth_token = request.cookies.get(AUTH_COOKIE_NAME)
                refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

                if auth_token:
                    try:
                        username = self._token_handler.decode_auth_token(auth_token)
                        self._token_handler.delete_token(p_token=auth_token, p_deletion_time=datetime.datetime.utcnow())
                        self._logger.info(f"User {username} logged out successfully.")

                    except TokenException as e:
                        self._logger.warn(f"Exception '{e!s}' while deleting access token {auth_token}")

                    if refresh_token is not None:
                        try:
                            self._token_handler.decode_auth_token(refresh_token, p_is_refresh=True)
                            self._token_handler.delete_token(p_token=refresh_token,
                                                             p_deletion_time=datetime.datetime.utcnow())

                        except TokenException as e:
                            self._logger.warn(f"Exception '{e!s}' while deleting refresh token {refresh_token}")

                    result['message'] = 'Successfully logged out.'

        except Exception as e:
            http_status = 403
            error_details = str(e)

        if error_details is not None:
            result['status'] = "ERROR"
            result['error_details'] = error_details

        return jsonify(result), http_status

    def destroy(self):
        ANGULAR_AUTH_BLUEPRINT_ADAPTER.unassign_view_handler_instances()
