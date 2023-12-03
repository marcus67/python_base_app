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

import datetime

from python_base_app.base_token_handler import BaseTokenHandlerConfigModel, TokenException, BaseTokenHandler
from python_base_app.simple_token_handler import SimpleTokenHandler
from python_base_app.test import base_test

SOME_USER = "some-user"
SECRET_KEY = "SOME_SEC_RET"

class TestBaseTokenHandler(base_test.BaseTestCase):

    def getDefaultTokenHandler(self, p_max_token_age_in_days = 365, p_token_life_in_minutes = 60) -> BaseTokenHandler:
        token_handler_config = BaseTokenHandlerConfigModel()
        token_handler_config.token_life_in_minutes = p_token_life_in_minutes
        token_handler_config.max_token_age_in_days = p_max_token_age_in_days
        return SimpleTokenHandler(p_config=token_handler_config, p_secret_key=SECRET_KEY)


    def testCreateToken(self):

        token_handler = self.getDefaultTokenHandler()
        id = SOME_USER

        token = token_handler.create_token(p_id=id)

        self.assertIsNotNone(token)

    def testCreateAndDecodeValidToken(self):

        token_handler = self.getDefaultTokenHandler()
        id = "some-user"

        token = token_handler.create_token(p_id=id)

        self.assertIsNotNone(token)

        result = token_handler.decode_auth_token(p_token=token)

        self.assertIsNotNone(result)
        self.assertEqual(id, result)

    def testCreateAndDecodeCorruptedToken(self):

        token_handler = self.getDefaultTokenHandler()
        id = "some-user"

        token = token_handler.create_token(p_id=id)

        self.assertIsNotNone(token)

        with self.assertRaises(TokenException) as e:
            token_handler.decode_auth_token(p_token=token + "x")

        self.assertIn("Invalid token", str(e.exception))

    def testCreateAndDecodeExpiredToken(self):

        token_handler = self.getDefaultTokenHandler(p_token_life_in_minutes=0)
        id = "some-user"

        reference_time = datetime.datetime.strptime("23:45:00 01.01.2023", "%H:%M:%S %d.%m.%Y")
        token = token_handler.create_token(p_id=id, p_reference_time=reference_time)
        self.assertIsNotNone(token)

        token_handler._secret_key = SECRET_KEY

        with self.assertRaises(TokenException) as e:
            token_handler.decode_auth_token(p_token=token)

        self.assertIn("expired", str(e.exception))

    def testCreateAndDecodeTokenInvalidSecret(self):

        token_handler = self.getDefaultTokenHandler()
        id = "some-user"

        token = token_handler.create_token(p_id=id)

        self.assertIsNotNone(token)

        token_handler._secret_key = SECRET_KEY + "x"

        with self.assertRaises(TokenException) as e:
            token_handler.decode_auth_token(p_token=token)

        self.assertIn("Invalid token", str(e.exception))


    def testCreateAndDecodeTokenAfterLogout(self):

        token_handler = self.getDefaultTokenHandler()
        id = "some-user"

        token = token_handler.create_token(p_id=id)

        self.assertIsNotNone(token)

        result = token_handler.decode_auth_token(p_token=token)

        self.assertIsNotNone(result)
        self.assertEqual(id, result)

        token_handler.delete_token(p_token=token)

        with self.assertRaises(TokenException) as e:
            token_handler.decode_auth_token(p_token=token)

        self.assertIn("blacklisted", str(e.exception))

    def testCreateAndDecodeTokenAfterLogoutAndNoCleanup(self):

        token_handler = self.getDefaultTokenHandler(p_max_token_age_in_days=2,
                                                    p_token_life_in_minutes=25*60 # a little more than 1 day
                                                    )
        id = "some-user"

        reference_time = datetime.datetime.utcnow()
        creation_time = reference_time + datetime.timedelta(days=-1)
        deletion_time = creation_time + datetime.timedelta(seconds=1)
        token = token_handler.create_token(p_id=id, p_reference_time=creation_time)

        self.assertIsNotNone(token)

        result = token_handler.decode_auth_token(p_token=token)

        self.assertIsNotNone(result)
        self.assertEqual(id, result)

        token_handler.delete_token(p_token=token, p_deletion_time=deletion_time)

        count = token_handler.cleanup(p_reference_time=reference_time)

        self.assertEqual(0, count)

        with self.assertRaises(TokenException) as e:
            token_handler.decode_auth_token(p_token=token)

        self.assertIn("blacklisted", str(e.exception))

    def testCreateAndDecodeTokenAfterLogoutAndCleanup(self):

        token_handler = self.getDefaultTokenHandler(p_max_token_age_in_days=1,
                                                    p_token_life_in_minutes=49*60 # a little more than 2 days
                                                    )
        id = "some-user"

        reference_time = datetime.datetime.utcnow()
        creation_time = reference_time + datetime.timedelta(days=-2)
        deletion_time = creation_time + datetime.timedelta(seconds=1)
        token = token_handler.create_token(p_id=id, p_reference_time=creation_time)

        self.assertIsNotNone(token)

        result = token_handler.decode_auth_token(p_token=token)

        self.assertIsNotNone(result)
        self.assertEqual(id, result)

        token_handler.delete_token(p_token=token, p_deletion_time=deletion_time)

        count = token_handler.cleanup(p_reference_time=reference_time)

        self.assertEqual(1, count)

        result = token_handler.decode_auth_token(p_token=token)

        self.assertEqual(id, result)

