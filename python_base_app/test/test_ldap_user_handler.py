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

import unittest
import unittest.mock

import fakeldap

from python_base_app import ldap_user_handler
from python_base_app.test import base_test

SEARCH_BASE_DN = "dc=mydomain,dc=com"

BIND_DN = "cn=admin," + SEARCH_BASE_DN
BIND_PASSWORD = "ldaptest"

USER_BASE_CN = "ou=users," + SEARCH_BASE_DN

USER_1_DN = "cn=admin," + USER_BASE_CN
USER_1_UID_NUMBER = "1000"
USER_1_UID = "admin"
USER_1_PASSWORD = "$ecret"

USER_2_DN = "cn=non-admin," + USER_BASE_CN
USER_2_UID_NUMBER = "1001"
USER_2_UID = "non-admin"

GROUP_BASE_DN = "ou=groups," + SEARCH_BASE_DN

GROUP_SEARCH_BASE_DN = GROUP_BASE_DN

ADMIN_GROUP_NAME = "little-brother-admins"
ADMIN_GROUP_DN = "ou=" + ADMIN_GROUP_NAME + "," + GROUP_BASE_DN

USER_GROUP_NAME = "little-brother-users"
USER_GROUP_DN = "ou=" + USER_GROUP_NAME + "," + GROUP_BASE_DN

LDAP_TREE = {
    BIND_DN: {
        "userPassword": BIND_PASSWORD
    },
    USER_1_DN: {
        "userPassword": USER_1_PASSWORD
    }
}

USER_FILTER = ldap_user_handler.USER_FILTER_PATTERN.format(cls=ldap_user_handler.DEFAULT_LDAP_USER_OBJECT_CLASS)
ADMIN_GROUP_FILTER = \
    ldap_user_handler.GROUP_FILTER_PATTERN.format(cls=ldap_user_handler.DEFAULT_LDAP_GROUP_OBJECT_CLASS,
                                                  group=ADMIN_GROUP_NAME)
USER_GROUP_FILTER = \
    ldap_user_handler.GROUP_FILTER_PATTERN.format(cls=ldap_user_handler.DEFAULT_LDAP_GROUP_OBJECT_CLASS,
                                                  group=USER_GROUP_NAME)

RETURN_VALUES = [
    (
        'search_s', (SEARCH_BASE_DN, 2, USER_FILTER,
                     ", ".join(ldap_user_handler.USER_ATTRS), 0),
        [
            (USER_1_DN,
             {
                 "uid": [USER_1_UID.encode("utf-8")],
                 "uidNumber": [USER_1_UID_NUMBER.encode("utf-8")],
                 "userPassword": USER_1_PASSWORD
             }
             ),
            (USER_2_DN,
             {
                 "uid": [USER_2_UID.encode("utf-8")],
                 "uidNumber": [USER_2_UID_NUMBER.encode("utf-8")]
             }
             ),
        ]
    ),
    (
        'search_s', (GROUP_SEARCH_BASE_DN, 2, ADMIN_GROUP_FILTER,
                     ", ".join(ldap_user_handler.GROUP_ATTRS), 0),
        [
            (ADMIN_GROUP_DN,
             {
                 "memberUid": [USER_1_UID.encode("utf-8")],
             }
             )
        ]
    ),
    (
        'search_s', (GROUP_SEARCH_BASE_DN, 2, USER_GROUP_FILTER,
                     ", ".join(ldap_user_handler.GROUP_ATTRS), 0),
        [
            (USER_GROUP_DN,
             {
                 "memberUid": [USER_2_UID.encode("utf-8")],
             }
             )
        ]
    )
]


class TestLdapUserHandler(base_test.BaseTestCase):

    # See https://pypi.org/project/fakeldap/
    def setUp(self):
        # Patch where the ldap library is used:
        self.ldap_patcher = unittest.mock.patch('ldap.initialize')
        self.mock_ldap = self.ldap_patcher.start()
        self.mock = fakeldap.MockLDAP(LDAP_TREE)

        for prv in RETURN_VALUES:
            self.mock.set_return_value(prv[0], prv[1], prv[2])

        self.mock_ldap.return_value = self.mock

    def tearDown(self):
        self.mock.reset()
        self.mock_ldap.stop()

    def get_config(self):
        config = ldap_user_handler.LdapUserHandlerConfigModel()

        config.ldap_bind_dn = BIND_DN
        config.ldap_bind_password = BIND_PASSWORD
        config.ldap_search_base_dn = SEARCH_BASE_DN
        config.ldap_group_search_base_dn = GROUP_SEARCH_BASE_DN
        config.ldap_admin_group_name = ADMIN_GROUP_NAME

        return config

    def test_inactive_config(self):

        config = ldap_user_handler.LdapUserHandlerConfigModel()
        self.assertFalse(config.is_active())

    def test_active_config(self):

        config = self.get_config()
        self.assertTrue(config.is_active())

    def test_instantiation(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertIsNotNone(handler)

    def test_bind(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        con = handler.get_ldap_connection()

        self.assertIsNotNone(con)

    def test_retrieve_users(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        users = handler.users

        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)

        self.assertIn(USER_1_UID, users)
        user = users[USER_1_UID]
        self.assertEqual(user.uid_number, int(USER_1_UID_NUMBER))
        self.assertEqual(user.dn, USER_1_DN)

        self.assertIn(USER_2_UID, users)
        user = users[USER_2_UID]
        self.assertEqual(user.uid_number, int(USER_2_UID_NUMBER))
        self.assertEqual(user.dn, USER_2_DN)

    def test_list_users_without_user_group(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        users = handler.list_users()

        self.assertIsNotNone(users)
        self.assertEqual(len(users), 2)
        self.assertIn(USER_1_UID, users)
        self.assertIn(USER_2_UID, users)

    def test_list_users_with_user_group(self):

        config = self.get_config()
        config.ldap_user_group_name = USER_GROUP_NAME
        handler = ldap_user_handler.LdapUserHandler(p_config=config)

        users = handler.list_users()

        self.assertIsNotNone(users)
        self.assertEqual(len(users), 1)
        self.assertIn(USER_2_UID, users)

    def test_retrieve_admins(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        admin_group = handler.admin_group

        self.assertIsNotNone(admin_group)
        self.assertEqual(len(admin_group), 1)

        self.assertIn(USER_1_UID, admin_group)

    def test_get_valid_uid(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        users = handler.users

        for username, user in users.items():
            self.assertEqual(user.uid_number, handler.get_uid(p_username=username))

    def test_get_invalid_uid(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertIsNone(handler.get_uid(p_username="xxx"))

    def test_authenticate_non_existing_user(self):

        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertFalse(handler.authenticate(p_username="xxx", p_password="yyy"))

    def test_authenticate_valid_password(self):

        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertTrue(handler.authenticate(p_username=USER_1_UID, p_password=USER_1_PASSWORD))

    def test_authenticate_invalid_password(self):

        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertFalse(handler.authenticate(p_username=USER_1_UID, p_password=USER_1_PASSWORD + "x"))

    def test_is_valid_admin(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertTrue(handler.is_admin(p_username=USER_1_UID))

    def test_is_invalid_admin(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertFalse(handler.is_admin(p_username=USER_2_UID))

    def test_is_invalid_uid_super_branch(self):
        handler = ldap_user_handler.LdapUserHandler(p_config=self.get_config())

        self.assertFalse(handler.is_valid_uid(p_uid=100, p_username="xxx"))
