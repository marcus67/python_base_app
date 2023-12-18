# -*- coding: utf-8 -*-

#    Copyright (C) 2021-2023  Marcus Rickert
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
from json import dumps

import requests
from requests import Session

from python_base_app import base_app
from python_base_app import base_web_server
from python_base_app.angular_auth_view_handler \
    import ANGULAR_LOGIN_REL_URL, ANGULAR_STATUS_REL_URL, AngularAuthViewHandler, ANGULAR_BASE_URL, \
    ANGULAR_LOGOUT_REL_URL
from python_base_app.base_token_handler import BaseTokenHandlerConfigModel
from python_base_app.base_web_server import BaseWebServer
from python_base_app.index_view_handler import IndexViewHandler
from python_base_app.simple_token_handler import SimpleTokenHandler
from python_base_app.test import base_test
from python_base_app.test.test_unix_user_handler import ADMIN_USER, ADMIN_PASSWORD
from python_base_app.test.test_unix_user_handler import TestUnixUserHandler


class TestBaseWebServer(base_test.BaseTestCase):

    @classmethod
    def default_server(cls):

        config = base_web_server.BaseWebServerConfigModel()
        return TestBaseWebServer.server_with_config(config)

    @classmethod
    def server_with_config(cls, p_config) -> BaseWebServer:

        p_config.port = int(os.getenv("PING_API_SERVER_PORT", "6660"))
        p_config.app_secret = "SOME-GIBBERISH"

        user_handler = TestUnixUserHandler.create_dummy_unix_user_handler()
        token_handler_config = BaseTokenHandlerConfigModel()
        token_handler = SimpleTokenHandler(p_config=token_handler_config, p_secret_key="SOME_SEC_RET")

        server = BaseWebServer(p_config=p_config, p_name="BaseWebServer", p_user_handler=user_handler,
                               p_package_name=base_app.PACKAGE_NAME)
        _login_view_handler = AngularAuthViewHandler(p_user_handler=user_handler,
                                                     p_token_handler=token_handler,
                                                     p_app=server.app, p_url_prefix=p_config.base_url)
        server.register_view_handler(_login_view_handler)
        _index_view_handler = IndexViewHandler(p_app=server.app, p_url_prefix=p_config.base_url)
        server.register_view_handler(_index_view_handler)
        return server

    def test_api_health(self):

        default_server = None

        try:
            default_server = self.default_server()

            default_server.start_server()

            url = f"http://localhost:{default_server._config.port}/health"

            r = requests.get(url)

            self.assertIsNotNone(r.text)
            self.assertEqual(r.text, "ok")

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_auth_invalid_angular_auth_json(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)
            new_headers["Content-Type"] = "application/json"

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = dumps({'username': ADMIN_USER, 'password': ADMIN_PASSWORD})

            # corrupt JSON
            payload = payload.replace(",", ";")

            r = session.post(url, data=payload, headers=new_headers)

            self.assertEqual(400, r.status_code, "Status code is 400")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('Exception during login', error_details)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_auth_missing_angular_auth_json(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)
            new_headers["Content-Type"] = "text/plain"

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = dumps({'username': ADMIN_USER, 'password': ADMIN_PASSWORD})

            r = session.post(url, data=payload, headers=new_headers)

            self.assertEqual(400, r.status_code, "Status code is 400")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('No JSON found', error_details)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_auth_invalid_angular_auth_parameter(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'x' + 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload, headers=new_headers)

            self.assertEqual(400, r.status_code, "Status code is 400")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('Parameter missing', error_details)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_auth_valid_credentials(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload, headers=new_headers)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")
            self.assertIn('auth_token', payload)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_auth_invalid_credentials(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)

            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD + "x"}

            r = session.post(url, json=payload, headers=new_headers)

            self.assertEqual(401, r.status_code, "Status code is 401")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('wrong password', error_details)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_status_no_bearer_token(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)

            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url, headers=new_headers)

            self.assertEqual(401, r.status_code, "Status code is 401")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('bearer token missing', error_details)


        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_status_bearer_token_is_malformed(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)

            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)

            new_headers['Authorization'] = "hallo"

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url, headers=new_headers)

            self.assertEqual(401, r.status_code, "Status code is 401")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('bearer token malformed', error_details)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_status_bearer_token_is_invalid(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)

            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)

            new_headers['Authorization'] = "Bearer hallo"

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url, headers=new_headers)

            self.assertEqual(401, r.status_code, "Status code is 401")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('Invalid token', error_details)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()


    def test_status_with_valid_login(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            new_headers = self.get_csrf_header(default_server, session)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload, headers=new_headers)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")
            self.assertIn('auth_token', payload)

            auth_token = payload['auth_token']

            new_headers = self.get_csrf_header(default_server, session)

            new_headers['Authorization'] = f"Bearer {auth_token}"

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url, headers=new_headers)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")



        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_status_after_logout(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            # Login
            new_headers = self.get_csrf_header(default_server, session)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload, headers=new_headers)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")
            self.assertIn('auth_token', payload)

            auth_token = payload['auth_token']

            new_headers = self.get_csrf_header(default_server, session)

            # Check status after valid login
            new_headers['Authorization'] = f"Bearer {auth_token}"

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url, headers=new_headers)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")

            # Logout
            new_headers = self.get_csrf_header(default_server, session)
            new_headers['Authorization'] = f"Bearer {auth_token}"
            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGOUT_REL_URL}"

            r = session.post(url, headers=new_headers)

            self.assertEqual(200, r.status_code, "Status code is 200")

            # Check status after logout (MUST fail!)
            new_headers = self.get_csrf_header(default_server, session)

            new_headers['Authorization'] = f"Bearer {auth_token}"

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url, headers=new_headers)

            self.assertEqual(401, r.status_code, "Status code is 401")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('blacklisted', error_details)




        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def get_csrf_header(self, default_server, session):

        url = f"http://localhost:{default_server._config.port}/"
        r = session.get(url)
        header_name = default_server.app.config["WTF_CSRF_HEADERS"][0]
        self.assertIn(header_name, r.headers)
        csrf_token = r.headers[header_name]
        new_headers = {header_name: csrf_token}
        return new_headers
