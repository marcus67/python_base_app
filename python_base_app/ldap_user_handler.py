# -*- coding: utf-8 -*-

# Copyright (C) 2019-2021  Marcus Rickert
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

import ldap

from python_base_app import base_user_handler
from python_base_app import configuration

SECTION_NAME = "LdapUserHandler"

HANDLER_NAME = "ldap"

DEFAULT_LDAP_HOST = "localhost"
DEFAULT_LDAP_PORT = 389
DEFAULT_LDAP_USER_OBJECT_CLASS = "posixAccount"
DEFAULT_LDAP_GROUP_OBJECT_CLASS = "posixGroup"

DEFAULT_MIN_UID = 500
DEFAULT_MAX_UID = 65000
INVALID_SHELLS = ["/usr/sbin/nologin", "/bin/false"]


class LdapUserHandlerConfigModel(base_user_handler.BaseUserHandlerConfigModel):

    def __init__(self):
        super().__init__(p_section_name=SECTION_NAME)

        self.ldap_host = DEFAULT_LDAP_HOST
        self.ldap_port = DEFAULT_LDAP_PORT
        self.ldap_bind_dn = configuration.NONE_STRING
        self.ldap_bind_password = configuration.NONE_STRING
        self.ldap_search_base_dn = configuration.NONE_STRING
        self.ldap_user_group_name = configuration.NONE_STRING
        self.ldap_admin_group_name = configuration.NONE_STRING
        self.ldap_user_object_class = DEFAULT_LDAP_USER_OBJECT_CLASS
        self.ldap_group_object_class = DEFAULT_LDAP_GROUP_OBJECT_CLASS

        self.min_uid = DEFAULT_MIN_UID
        self.max_uid = DEFAULT_MAX_UID

    def is_active(self):
        return (self.ldap_bind_dn is not None and
                self.ldap_bind_password is not None and
                self.ldap_search_base_dn is not None and
                self.ldap_admin_group_name is not None)


class LdapUser(object):

    def __init__(self, p_uid, p_dn):
        self.uid = p_uid
        self.dn = p_dn


class LdapUserHandler(base_user_handler.BaseUserHandler):

    def __init__(self, p_config):

        super().__init__(p_config=p_config)

        self._config = p_config
        self._users = None
        self._user_group = None
        self._admin_group = None

        msg = "Using LDAP server at {url} with bind DN '{dn}'..."
        self._logger.info(msg.format(url=self.get_ldap_url(), dn=self._config.ldap_bind_dn))

        if self._config.ldap_admin_group_name:
            msg = "Using LDAP group '{admin_group}' for retrieving administrators..."
            self._logger.info(msg.format(admin_group=self._config.ldap_admin_group_name))

        if self._config.ldap_user_group_name:
            msg = "Using LDAP group '{user_group}' for retrieving users..."
            self._logger.info(msg.format(user_group=self._config.ldap_user_group_name))

    def get_ldap_url(self):

        url_pattern = "ldap://{host}:{port}"
        return url_pattern.format(host=self._config.ldap_host, port=self._config.ldap_port)

    def get_ldap_connection(self, p_bind_dn=None, p_bind_password=None):

        if p_bind_dn is None:
            p_bind_dn = self._config.ldap_bind_dn

        if p_bind_password is None:
            p_bind_password = self._config.ldap_bind_password

        con = ldap.initialize(self.get_ldap_url())
        result = con.simple_bind_s(p_bind_dn, p_bind_password)

        if result[0] != 97:
            raise Exception()  # todo

        return con

    def retrieve_group(self, p_group_dn):

        con = self.get_ldap_connection()

        filter_pattern = "( & (objectClass={cls}) (cn={group}) )"
        result = con.search_s(self._config.ldap_search_base_dn, ldap.SCOPE_SUBTREE,
                              filter_pattern.format(cls=self._config.ldap_group_object_class,
                                                    group=p_group_dn),
                              ["memberUid"])

        usernames = {entry.decode("utf-8") for entry in result[0][1]["memberUid"]}
        return usernames

    @property
    def user_group(self):

        if self._user_group is None:
            self._user_group = self.retrieve_group(p_group_dn=self._config.ldap_user_group_name)

        return self._user_group

    @property
    def admin_group(self):

        if self._admin_group is None:
            self._admin_group = self.retrieve_group(p_group_dn=self._config.ldap_admin_group_name)

        return self._admin_group

    def is_valid_uid(self, p_uid, p_username=None, p_password=None, p_shell=None):

        if not super().is_valid_uid(p_uid=p_uid, p_username=p_username, p_password=p_password, p_shell=p_shell):
            return False

        if self._config.ldap_user_group_name is not None:
            if p_username not in self.user_group:
                return False

        return True

    @property
    def users(self):

        if self._users is None:
            con = self.get_ldap_connection()

            filter_pattern = "(objectClass={cls})"
            result = con.search_s(self._config.ldap_search_base_dn, ldap.SCOPE_SUBTREE,
                                  filter_pattern.format(cls=self._config.ldap_user_object_class),
                                  ["uid", "uidNumber", "gecos"])

            self._users = {
                entry[1]["uid"][0].decode("utf-8") :
                    LdapUser(p_uid=int(entry[1]["uidNumber"][0].decode("utf-8")), p_dn=entry[0])
                for entry in result
            }

        return self._users

    def list_users(self):

        return [ username for username, user in self.users.items()
                 if self.is_valid_uid(p_uid=user.uid, p_username=username) ]

    def get_uid(self, p_username):

        ldap_user = self.users.get(p_username)

        if ldap_user is None:
            return None

        return ldap_user.uid

    def authenticate(self, p_username, p_password):

        ldap_user = self.users.get(p_username)

        if ldap_user is None:
            return False

        try:
            self.get_ldap_connection(p_bind_dn=ldap_user.dn, p_bind_password=p_password)

        except ldap.INVALID_CREDENTIALS:
            msg = "failed attempt to authenticate as user '{username}'"
            self._logger.warn(msg.format(username=p_username))
            return False

        return True

    def is_admin(self, p_username):

        return p_username in self.admin_group
