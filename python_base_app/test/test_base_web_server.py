# -*- coding: utf-8 -*-

#    Copyright (C) 2021  Marcus Rickert
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

import os

import requests

from python_base_app import base_app
from python_base_app import base_web_server
from python_base_app.test import base_test


class TestBaseWebServer(base_test.BaseTestCase):

    @classmethod
    def default_server(cls):

        config = base_web_server.BaseWebServerConfigModel()
        config.port = int(os.getenv("PING_API_SERVER_PORT", "6660"))
        server = base_web_server.BaseWebServer(p_config=config, p_name="BaseWebServer",
                                               p_package_name=base_app.PACKAGE_NAME)

        return server

    def test_api_health(self):

        default_server = None

        try:
            default_server = self.default_server()

            default_server.start_server()

            url = "http://localhost:{port}/health"
            r = requests.get(url.format(port=default_server._config.port))

            self.assertIsNotNone(r.text)
            self.assertEqual(r.text, "ok")

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()
