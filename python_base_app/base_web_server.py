# -*- coding: utf-8 -*-

#    Copyright (C) 2019  Marcus Rickert
#
#    See https://github.com/marcus67/python_base_app
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging
import threading
import time
import urllib.parse
from os.path import join

import flask.globals
import flask.wrappers
import flask_login

import flask_helpers

from python_base_app import actuator
from python_base_app import auth_view_handler
from python_base_app import configuration
from python_base_app import log_handling
from python_base_app import tools

DEFAULT_BASE_URL = ''
DEFAULT_INTERNAL_BASE_URL = ''

_ = lambda x: x


class BaseWebServerConfigModel(configuration.ConfigModel):

    def __init__(self, p_section_name):
        super(BaseWebServerConfigModel, self).__init__(p_section_name)
        self.scheme = "http"
        self.host = "0.0.0.0"
        self.port = configuration.NONE_INTEGER
        self.base_url = DEFAULT_BASE_URL
        self.internal_base_url = DEFAULT_INTERNAL_BASE_URL
        self.health_url = None

        self.admin_username = "admin"
        self.admin_password = configuration.NONE_STRING
        self.app_secret = configuration.NONE_STRING

    def is_active(self):
        return self.port is not None


class BaseWebServer(object):

    def __init__(self, p_name, p_config, p_package_name, p_use_login_manager=False,
                 p_login_view=None, p_logged_out_endpoint=None):

        self._login_manager = None
        self._flask_stopper = None
        self._auth_view_handler = None
        self._server_started = False

        self._name = p_name
        self._config = p_config
        self._login_view = p_login_view

        # self._blueprint = flask.Blueprint("main", python_base_app.__name__)

        if p_package_name is None:
            raise configuration.ConfigurationException("HttpServer: p_package_name must not be None")

        self._logger = log_handling.get_logger(self.__class__.__name__)

        self._app = flask.Flask(p_package_name)
        self._flask_stopper = flask_helpers.FlaskStopper(p_app=self._app, p_logger=self._logger)

        self._app.config["APPLICATION_ROOT"] = self._config.base_url

        if p_use_login_manager:
            tools.check_config_value(p_config=self._config, p_config_attribute_name="admin_username")
            tools.check_config_value(p_config=self._config, p_config_attribute_name="admin_password")
            tools.check_config_value(p_config=self._config, p_config_attribute_name="app_secret")

            self._auth_view_handler = auth_view_handler.AuthViewHandler(
                p_admin_username=self._config.admin_username, p_admin_password=self._config.admin_password,
                p_app=self._app, p_logged_out_endpoint=p_logged_out_endpoint,
                p_url_prefix=self._config.base_url,
                p_login_view=p_login_view)

            self._app.config.update(SECRET_KEY=self._config.app_secret)

        self._server_exception = None

        # Install the actuator handler for the health check
        self._actuator_view_handler = actuator.ActuatorViewHandler(p_app=self._app, p_url_prefix=self._config.internal_base_url)

        logger = log_handling.get_logger("werkzeug")
        logger.setLevel(logging.WARNING)

        logger = log_handling.get_logger("sqlalchemy.engine")
        logger.setLevel(logging.WARNING)

    def destroy(self):
        self._actuator_view_handler.destroy()
        self._flask_stopper.destroy()

        if self._auth_view_handler is not None:
            self._auth_view_handler.destroy()

    def add_url_rule(self, p_rel_url, p_endpoint, p_view_method, p_blueprint=None,
                     p_methods=None,
                     p_login_required=False):

        if p_login_required:
            p_view_method = flask_login.login_required(p_view_method)

        blueprint = p_blueprint if p_blueprint is not None else self._blueprint

        blueprint.add_url_rule(join(self._config.base_url, p_rel_url),
                               p_endpoint,
                               p_view_method,
                               methods=p_methods)

    def get_url(self, p_rel_url='', p_internal=False, p_simple=False):

        return urllib.parse.urlunsplit(
            (
                self._config.scheme,
                "%s:%d" % (self._config.host, self._config.port),
                join(self._config.base_url, p_rel_url),
                None,
                None
            ))

    def start_server(self):

        tools.check_config_value(p_config=self._config, p_config_attribute_name="port")

        self._process = threading.Thread(target=self.run)
        self._process.start()
        time.sleep(1)

        if self._server_exception is not None:
            raise self._server_exception

        self._server_started = True

    def stop_server(self):

        if self._server_started and self._flask_stopper is not None:
            fmt = "Stopping web server %s..." % self._name
            self._logger.info(fmt)

            self._flask_stopper.stop(host=self._config.host, port=self._config.port)

            fmt = "Waiting for the server thread to terminate"
            self._logger.info(fmt)

            self._process.join()

            fmt = "HTTP server '%s' shut down successfully" % self._name
            self._logger.info(fmt)

    def run(self):

        tools.check_config_value(p_config=self._config, p_config_attribute_name="host")

        fmt = "Starting web server '{name}' on {address}:{port}"
        self._logger.info(fmt.format(name=self._name, address=self._config.host, port=self._config.port))

        # See https://stackoverflow.com/questions/14814201/can-i-serve-multiple-clients-using-just-flask-app-run-as-standalone
        try:
            self._app.run(port=self._config.port, host=self._config.host, threaded=True)

        except Exception as e:
            fmt = "Exception '%s' while starting web server %s" % (str(e), self._name)
            self._logger.error(fmt)

            self._server_exception = e
            raise e

    def get_authenication_info(self):

        tmp = flask_login.current_user
        return {
            "is_authenticated": flask_login.current_user is not None and flask_login.current_user.is_authenticated,
            "username": getattr(flask_login.current_user, "username",
                                "NO USER") if flask_login.current_user is not None else "NO USER"}
