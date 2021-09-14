# -*- coding: utf-8 -*-

#    Copyright (C) 2019-2021  Marcus Rickert
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
from flask_wtf import CSRFProtect
from secure import Secure

import some_flask_helpers
from python_base_app import actuator
from python_base_app import auth_view_handler
from python_base_app import configuration
from python_base_app import log_handling
from python_base_app import tools

DEFAULT_BASE_URL = ''
DEFAULT_INTERNAL_BASE_URL = ''

_ = lambda x: x

DUMMY_SECTION_NAME = "BaseWebServer"

# see https://improveandrepeat.com/2020/10/python-friday-43-add-security-headers-to-your-flask-application/
# see https://secure.readthedocs.io/en/latest/frameworks.html#flask

secure_headers = Secure()


def set_secure_headers(response):
    secure_headers.framework.flask(response)
    return response


class BaseWebServerConfigModel(configuration.ConfigModel):

    def __init__(self, p_section_name=DUMMY_SECTION_NAME):
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

    def __init__(self, p_name, p_config, p_package_name, p_user_handler=None,
                 p_login_view=None, p_logged_out_endpoint=None):

        self._login_manager = None
        self._flask_stopper = None
        self._auth_view_handler = None
        self._server_started = False
        self._user_handler = p_user_handler
        self._csrf = None

        self._name = p_name
        self._config = p_config
        self._login_view = p_login_view

        if p_package_name is None:
            raise configuration.ConfigurationException("HttpServer: p_package_name must not be None")

        self._logger = log_handling.get_logger(self.__class__.__name__)

        self._app = flask.Flask(p_package_name)

        # see https://improveandrepeat.com/2020/10/python-friday-43-add-security-headers-to-your-flask-application/
        # see https://secure.readthedocs.io/en/latest/frameworks.html#flask
        self._app.after_request(set_secure_headers)

        # see https://stackoverflow.com/questions/62992831/python-session-samesite-none-not-being-set
        # see https://flask.palletsprojects.com/en/2.0.x/security/#security-cookie
        self._app.config['SESSION_COOKIE_SAMESITE'] = "Strict"

        self._flask_stopper = some_flask_helpers.FlaskStopper(p_app=self._app, p_logger=self._logger)

        self._app.config["APPLICATION_ROOT"] = self._config.base_url

        if self._user_handler is not None:
            tools.check_config_value(p_config=self._config, p_config_attribute_name="app_secret")

            self._auth_view_handler = auth_view_handler.AuthViewHandler(
                p_user_handler=self._user_handler,
                p_app=self._app, p_logged_out_endpoint=p_logged_out_endpoint,
                p_url_prefix=self._config.base_url,
                p_login_view=p_login_view)

            # Activate CSRF protection
            self._app.config.update(SECRET_KEY=self._config.app_secret)
            self._csrf = CSRFProtect()
            self._csrf.init_app(self._app)

        self._server_exception = None

        # Install the actuator handler for the health check
        self._actuator_view_handler = actuator.ActuatorViewHandler(p_app=self._app,
                                                                   p_url_prefix=self._config.internal_base_url)

        logger = log_handling.get_logger("werkzeug")
        logger.setLevel(logging.WARNING)

        logger = log_handling.get_logger("sqlalchemy.engine")
        logger.setLevel(logging.WARNING)

    def destroy(self):
        self._actuator_view_handler.destroy()
        self._flask_stopper.destroy()

        if self._auth_view_handler is not None:
            self._auth_view_handler.destroy()

    def add_url_rule(self, p_rel_url, p_endpoint, p_view_method, p_blueprint,
                     p_methods=None,
                     p_login_required=False):

        if p_login_required:
            p_view_method = flask_login.login_required(p_view_method)

        p_blueprint.add_url_rule(join(self._config.base_url, p_rel_url),
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

            self._process.join(timeout=3)

            fmt = "HTTP server '%s' shut down successfully" % self._name
            self._logger.info(fmt)

    def run(self):

        tools.check_config_value(p_config=self._config, p_config_attribute_name="host")

        fmt = "Starting web server '{name}' on {address}:{port}{base_url}"
        self._logger.info(fmt.format(name=self._name, address=self._config.host, port=self._config.port,
                                     base_url=self._config.base_url))

        # See https://stackoverflow.com/questions/14814201/can-i-serve-multiple-clients-using-just-flask-app-run-as-standalone
        try:
            self._app.run(port=self._config.port, host=self._config.host, threaded=True)

        except Exception as e:
            fmt = "Exception '%s' while starting web server %s" % (str(e), self._name)
            self._logger.error(fmt)

            self._server_exception = e
            raise e

    @classmethod
    def get_authentication_info(cls):

        return {
            "is_authenticated": flask_login.current_user is not None and flask_login.current_user.is_authenticated,
            "username": getattr(flask_login.current_user, "username",
                                "NO USER") if flask_login.current_user is not None else "NO USER"}
