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

import unittest.mock

from python_base_app import configuration
from python_base_app import unix_user_handler
from python_base_app.test import base_test

SEARCH_BASE_DN = "dc=mydomain,dc=com"

ADMIN_USER = "admin"
ADMIN_PASSWORD = "hello!"

USER_1_UID_NUMBER = "1000"
USER_1_UID = "admin"
USER_1_PASSWORD = "$ecret"

USER_2_UID_NUMBER = "1001"
USER_2_UID = "non-admin"
USER_2_PASSWORD = "0ther$ecret"

USER_3_UID_NUMBER = "100"
USER_3_UID = "special-user"
USER_3_PASSWORD = "0ther$ecret"

CONFIG_USER_LIST = USER_1_UID + ":" + USER_1_UID_NUMBER + "," + USER_2_UID + ":" + USER_2_UID_NUMBER


class FakePasswordEntry(object):

    def __init__(self, p_uid, p_username, p_password, p_shell):
        self.pw_uid = p_uid
        self.pw_name = p_username
        self.pw_passwd = p_password
        self.pw_shell = p_shell


FAKE_USER_MAP = {
    USER_1_UID: FakePasswordEntry(p_uid=int(USER_1_UID_NUMBER), p_username=USER_1_UID, p_password=USER_1_PASSWORD,
                                  p_shell="/bin/bash"),
    USER_2_UID: FakePasswordEntry(p_uid=int(USER_2_UID_NUMBER), p_username=USER_2_UID, p_password=USER_2_PASSWORD,
                                  p_shell="/bin/bash"),
    USER_3_UID: FakePasswordEntry(p_uid=int(USER_3_UID_NUMBER), p_username=USER_3_UID, p_password=USER_3_PASSWORD,
                                  p_shell="/bin/bash"),
}


def fake_getpwall():
    return FAKE_USER_MAP.values()


def fake_getpwnam(p_username):
    return FAKE_USER_MAP.get(p_username)


class TestUnixUserHandler(base_test.BaseTestCase):

    @classmethod
    def create_dummy_unix_user_handler(cls):
        config = unix_user_handler.UnixUserHandlerConfigModel()
        config.admin_username = ADMIN_USER
        config.admin_password = ADMIN_PASSWORD
        config.user_list = CONFIG_USER_LIST

        return unix_user_handler.UnixUserHandler(p_config=config)

    # See https://pypi.org/project/fakeunix/
    def setUp(self):
        # Patch where the unix library is used:
        self.getpwall_patcher = unittest.mock.patch('pwd.getpwall')
        self.mock_getpwall = self.getpwall_patcher.start()
        self.mock_getpwall.return_value = fake_getpwall()

        self.getpwnam_patcher = unittest.mock.patch('pwd.getpwnam')
        self.mock_getpwnam = self.getpwnam_patcher.start()
        self.mock_getpwnam.side_effect = fake_getpwnam

    def tearDown(self):
        self.mock_getpwall.stop()
        self.mock_getpwnam.stop()

    @classmethod
    def get_config(cls, p_user_list=None):
        config = unix_user_handler.UnixUserHandlerConfigModel()

        config.admin_username = USER_1_UID
        config.admin_password = USER_1_PASSWORD
        config.user_list = p_user_list

        return config

    def test_inactive_config(self):
        config = unix_user_handler.UnixUserHandlerConfigModel()
        self.assertFalse(config.is_active())

    def test_active_config(self):
        config = self.get_config()
        self.assertTrue(config.is_active())

    def test_instantiation(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config())

        self.assertIsNotNone(handler)

    def test_instantiation_invalid_user_list(self):
        config = self.get_config(p_user_list="xxx:yyy")

        with self.assertRaises(configuration.ConfigurationException):
            unix_user_handler.UnixUserHandler(p_config=config)

    def test_list_users(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        users = handler.list_users()

        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)
        self.assertIn(USER_1_UID, users)
        self.assertIn(USER_2_UID, users)

    def test_list_users_without_user_list(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config())

        users = handler.list_users()

        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)
        self.assertIn(USER_1_UID, users)
        self.assertIn(USER_2_UID, users)

    def test_get_valid_uid(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertEqual(int(USER_1_UID_NUMBER), handler.get_uid(p_username=USER_1_UID))
        self.assertEqual(int(USER_2_UID_NUMBER), handler.get_uid(p_username=USER_2_UID))

    def test_get_valid_uid_without_user_list(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config())

        self.assertEqual(int(USER_1_UID_NUMBER), handler.get_uid(p_username=USER_1_UID))
        self.assertEqual(int(USER_2_UID_NUMBER), handler.get_uid(p_username=USER_2_UID))

    def test_get_invalid_uid(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertIsNone(handler.get_uid(p_username="xxx"))

    def test_get_invalid_uid_without_user_list(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config())

        self.assertIsNone(handler.get_uid(p_username="xxx"))

    def test_authenticate_non_admin_user(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertFalse(handler.authenticate(p_username=USER_2_UID, p_password=USER_2_PASSWORD))

    def test_authenticate_admin_valid_password(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertTrue(handler.authenticate(p_username=USER_1_UID, p_password=USER_1_PASSWORD))

    def test_authenticate_admin_invalid_password(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertFalse(handler.authenticate(p_username=USER_1_UID, p_password=USER_1_PASSWORD + "x"))

    def test_is_valid_admin(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertTrue(handler.is_admin(p_username=USER_1_UID))

    def test_is_invalid_admin(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertFalse(handler.is_admin(p_username=USER_2_UID))

    def test_is_invalid_uid_super_branch(self):
        handler = unix_user_handler.UnixUserHandler(p_config=self.get_config(p_user_list=CONFIG_USER_LIST))

        self.assertFalse(handler.is_valid_uid(p_uid=100, p_username="xxx"))
