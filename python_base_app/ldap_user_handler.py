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
import datetime

import ldap

from python_base_app import base_user_handler, tools
from python_base_app import configuration

SECTION_NAME = "LdapUserHandler"

HANDLER_NAME = "ldap"

DEFAULT_LDAP_HOST = "localhost"
DEFAULT_LDAP_PORT = 389
DEFAULT_LDAP_USER_OBJECT_CLASS = "posixAccount"
DEFAULT_LDAP_GROUP_OBJECT_CLASS = "posixGroup"

DEFAULT_CACHE_TIMEOUT_IN_MINUTES = 1

USER_FILTER_PATTERN = "(objectClass={cls})"
USER_ATTRS = ["uid", "uidNumber", "gecos"]

GROUP_FILTER_PATTERN = "( & (objectClass={cls}) (cn={group}) )"
GROUP_ATTRS = ["memberUid"]


class LdapUserHandlerConfigModel(base_user_handler.BaseUserHandlerConfigModel):

    def __init__(self):
        super().__init__(p_section_name=SECTION_NAME)

        self.ldap_host = DEFAULT_LDAP_HOST
        self.ldap_port = DEFAULT_LDAP_PORT
        self.ldap_bind_dn = configuration.NONE_STRING
        self.ldap_bind_password = configuration.NONE_STRING
        self.ldap_search_base_dn = configuration.NONE_STRING
        self.ldap_group_search_base_dn = configuration.NONE_STRING
        self.ldap_user_group_name = configuration.NONE_STRING
        self.ldap_admin_group_name = configuration.NONE_STRING
        self.ldap_user_object_class = DEFAULT_LDAP_USER_OBJECT_CLASS
        self.ldap_group_object_class = DEFAULT_LDAP_GROUP_OBJECT_CLASS
        self.cache_timeout_in_minutes = DEFAULT_CACHE_TIMEOUT_IN_MINUTES

    def is_active(self):
        return (self.ldap_bind_dn is not None and
                self.ldap_bind_password is not None and
                self.ldap_search_base_dn is not None and
                self.ldap_admin_group_name is not None)


class LdapUser(object):

    def __init__(self, p_uid_number, p_dn):
        self.uid_number = p_uid_number
        self.dn = p_dn


class LdapUserHandler(base_user_handler.BaseUserHandler):

    def __init__(self, p_config, p_exclude_user_list=None):

        super().__init__(p_config=p_config, p_exclude_user_list=p_exclude_user_list)

        self._config = p_config
        self._users = None
        self._user_group = None
        self._admin_group = None
        self._last_query_time = None

        msg = "Using LDAP server at {url} with bind DN '{dn}'..."
        self._logger.info(msg.format(url=self.get_ldap_url(), dn=self._config.ldap_bind_dn))

        msg = "Using LDAP group '{admin_group}' for retrieving administrators..."
        self._logger.info(msg.format(admin_group=self._config.ldap_admin_group_name))

        # Test-load group to detect misconfiguration during startup
        grp = self.admin_group
        msg = "Valid administrators: {user_names}"
        self._logger.info(msg.format(user_names=", ".join(grp)))

        if self._config.ldap_user_group_name:
            msg = "Using LDAP group '{user_group}' for retrieving users..."
            self._logger.info(msg.format(user_group=self._config.ldap_user_group_name))

            # Test-load group to detect misconfiguration during startup
            grp = self.user_group
            msg = "Valid users: {user_names}"
            self._logger.info(msg.format(user_names=", ".join(grp)))

    def check_cache(self):

        current_time = tools.get_current_time()

        if self._last_query_time is None or current_time > self._last_query_time:
            self._last_query_time = current_time + datetime.timedelta(minutes=self._config.cache_timeout_in_minutes)
            self._user_group = None
            self._users = None
            self._admin_group = None

    def get_ldap_url(self):

        url_pattern = "ldap://{host}:{port}"
        return url_pattern.format(host=self._config.ldap_host, port=self._config.ldap_port)

    def get_ldap_connection(self, p_bind_dn=None, p_bind_password=None):

        if p_bind_dn is None:
            p_bind_dn = self._config.ldap_bind_dn

        if p_bind_password is None:
            p_bind_password = self._config.ldap_bind_password

        con = ldap.initialize(self.get_ldap_url())

        try:
            result = con.simple_bind_s(p_bind_dn, p_bind_password)

            if result[0] != 97:
                msg = "error {result} while opening LDAP server at {url}"
                raise configuration.ConfigurationException(msg.format(result=result[0], url=self.get_ldap_url()))

        except ldap.INVALID_CREDENTIALS:
            raise

        except Exception as e:
            msg = "exception '{msg}' while opening LDAP server at {url}"
            raise configuration.ConfigurationException(msg.format(msg=str(e), url=self.get_ldap_url()))

        return con

    def retrieve_group(self, p_group_dn):

        search_base_dn = self._config.ldap_group_search_base_dn \
            if self._config.ldap_group_search_base_dn is not None else self._config.ldap_search_base_dn

        con = self.get_ldap_connection()

        try:
            result = con.search_s(search_base_dn, ldap.SCOPE_SUBTREE,
                                  GROUP_FILTER_PATTERN.format(cls=self._config.ldap_group_object_class,
                                                              group=p_group_dn),
                                  GROUP_ATTRS)

        except Exception as e:
            msg = "exception '{exception}' while searching for LDAP group '{group_dn}' in sub tree '{dn}'"
            raise configuration.ConfigurationException(msg.format(exception=str(e),
                                                                  group_dn=p_group_dn,
                                                                  dn=search_base_dn))


        if len(result) == 0:
            msg = "cannot find LDAP group '{group_dn}' in sub tree '{dn}'"
            raise configuration.ConfigurationException(msg.format(group_dn=p_group_dn,
                                                                  dn=search_base_dn))

        msg = "retrieved LDAP group '{group_dn}' in sub tree '{dn}'"
        self._logger.info(msg.format(group_dn=p_group_dn, dn=search_base_dn))

        usernames = {entry.decode("utf-8") for entry in result[0][1]["memberUid"]}
        return usernames

    @property
    def user_group(self):

        self.check_cache()

        if self._user_group is None:
            self._user_group = self.retrieve_group(p_group_dn=self._config.ldap_user_group_name)

        return self._user_group

    @property
    def admin_group(self):

        self.check_cache()

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

        self.check_cache()

        if self._users is None:
            con = self.get_ldap_connection()

            result = con.search_s(self._config.ldap_search_base_dn, ldap.SCOPE_SUBTREE,
                                  USER_FILTER_PATTERN.format(cls=self._config.ldap_user_object_class),
                                  USER_ATTRS)

            self._users = {
                entry[1]["uid"][0].decode("utf-8"):
                    LdapUser(p_uid_number=int(entry[1]["uidNumber"][0].decode("utf-8")), p_dn=entry[0])
                for entry in result
            }

            msg = "retrieved LDAP users in sub tree '{dn}'"
            self._logger.info(msg.format(dn=self._config.ldap_search_base_dn))

        return self._users

    def list_users(self):

        return [username for username, user in self.users.items()
                if self.is_valid_uid(p_uid=user.uid_number, p_username=username)]

    def get_uid(self, p_username):

        ldap_user = self.users.get(p_username)

        if ldap_user is None:
            return None

        return ldap_user.uid_number

    def authenticate(self, p_username, p_password):

        ldap_user = self.users.get(p_username)

        if ldap_user is None:
            return False

        try:
            self.get_ldap_connection(p_bind_dn=ldap_user.dn, p_bind_password=p_password)

        except ldap.INVALID_CREDENTIALS:
            return False

        except Exception as e:
            msg = "failed attempt to authenticate as user '{username}' due to '{msg}'"
            self._logger.warning(msg.format(username=p_username, msg=str(e)))
            raise e

        return True

    def is_admin(self, p_username):

        return p_username in self.admin_group
