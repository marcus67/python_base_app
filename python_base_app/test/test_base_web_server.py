# -*- coding: utf-8 -*-

#    Copyright (C) 2021-2025  Marcus Rickert
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
from typing import Callable

import requests
from requests import Session

from python_base_app import base_app
from python_base_app import base_web_server
from python_base_app.angular_auth_view_handler \
    import ANGULAR_LOGIN_REL_URL, ANGULAR_STATUS_REL_URL, AngularAuthViewHandler, \
    ANGULAR_LOGOUT_REL_URL, AUTH_COOKIE_NAME
from python_base_app.base_token_handler import BaseTokenHandlerConfigModel
from python_base_app.base_web_server import BaseWebServer
from python_base_app.simple_token_handler import SimpleTokenHandler
from python_base_app.test import base_test
from python_base_app.test.test_unix_user_handler import ADMIN_USER, ADMIN_PASSWORD, ADMIN_USER_ID
from python_base_app.test.test_unix_user_handler import TestUnixUserHandler


class TestBaseWebServer(base_test.BaseTestCase):

    @classmethod
    def default_server(cls):

        config = base_web_server.BaseWebServerConfigModel()
        return TestBaseWebServer.server_with_config(config)

    @classmethod
    def server_with_config(cls, p_config, p_auth_result_processor:Callable[[dict], int|None] = None) -> BaseWebServer:

        p_config.port = int(os.getenv("PING_API_SERVER_PORT", "6660"))
        p_config.app_secret = "SOME-GIBBERISH"

        user_handler = TestUnixUserHandler.create_dummy_unix_user_handler()
        token_handler_config = BaseTokenHandlerConfigModel()
        token_handler = SimpleTokenHandler(p_config=token_handler_config, p_secret_key="SOME_SEC_RET")

        server = BaseWebServer(p_config=p_config, p_name="BaseWebServer", p_user_handler=user_handler,
                               p_package_name=base_app.PACKAGE_NAME)
        _login_view_handler = AngularAuthViewHandler(p_user_handler=user_handler,
                                                     p_token_handler=token_handler,
                                                     p_app=server.app, p_url_prefix=p_config.base_url,
                                                     p_auth_result_processor=p_auth_result_processor)
        server.register_view_handler(_login_view_handler)

        if not p_config.use_csrf:
            server.csrf_exempt_blueprint(_login_view_handler.blueprint)

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
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            new_headers = {"Content-Type": "application/json"}

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
            self.assertIn('General exception during login', error_details)

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
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            new_headers = {"Content-Type": "text/plain"}

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
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'x' + 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload)

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
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")
            self.assertIn(AUTH_COOKIE_NAME, r.cookies)

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
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)

            default_server.start_server()

            session = Session()

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD + "x"}

            r = session.post(url, json=payload)

            self.assertEqual(401, r.status_code, "Status code is 401")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('wrong password', error_details)
            self.assertNotIn(AUTH_COOKIE_NAME, r.cookies)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_status_no_auth_cookie(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)

            default_server.start_server()

            session = Session()

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url)

            self.assertEqual(401, r.status_code, "Status code is 401")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "ERROR")
            self.assertIn('error_details', payload)
            error_details = payload['error_details']
            self.assertIn('auth cookie missing', error_details)

        except Exception as e:
            raise e

        finally:
            if default_server is not None:
                default_server.stop_server()
                default_server.destroy()

    def test_status_token_is_invalid(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)

            default_server.start_server()

            session = Session()

            cookies = {AUTH_COOKIE_NAME: "hallo"}

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url, cookies=cookies)

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
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")

            self.assertIsNotNone(r.cookies.get(AUTH_COOKIE_NAME), "Cookie was returned")

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url)

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

    def add_user_id_to_authorization_result(self, p_authorization_result:dict):
        self.assertEqual(ADMIN_USER, p_authorization_result["username"])
        p_authorization_result["user_id"] = ADMIN_USER_ID

    def test_status_with_valid_login_and_result_processing(self):

        default_server = None

        try:
            config = base_web_server.BaseWebServerConfigModel()
            config.use_csrf = False



            default_server = self.server_with_config(p_config=config,
                                                     p_auth_result_processor=lambda p_authorization_result:
                                                     self.add_user_id_to_authorization_result(
                                                         p_authorization_result)
                                                     )
            default_server.start_server()

            session = Session()

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")
            user_id = payload.get("user_id")
            self.assertIsNotNone(user_id)
            self.assertEqual(ADMIN_USER_ID, user_id)


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
            config.use_csrf = False

            default_server = self.server_with_config(p_config=config)
            default_server.start_server()

            session = Session()

            # Login

            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGIN_REL_URL}"
            payload = {'username': ADMIN_USER, 'password': ADMIN_PASSWORD}

            r = session.post(url, json=payload)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")
            self.assertIn(AUTH_COOKIE_NAME, r.cookies)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url)

            self.assertEqual(200, r.status_code, "Status code is 200")

            self.assertIsNotNone(r.json())
            payload = r.json()
            self.assertEqual(payload['status'], "OK")

            # Logout
            url = f"http://localhost:{default_server._config.port}{ANGULAR_LOGOUT_REL_URL}"

            r = session.post(url)

            self.assertEqual(200, r.status_code, "Status code is 200")

            # Check status after logout (MUST fail!)

            url = f"http://localhost:{default_server._config.port}{ANGULAR_STATUS_REL_URL}"

            r = session.get(url)

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

    def test_refresh(self):

        # TODO: test cases for refresh!
        self.assertFalse(False)
