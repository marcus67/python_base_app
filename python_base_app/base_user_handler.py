# -*- coding: utf-8 -*-

# Copyright (C) 2019  Marcus Rickert
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

import abc

from python_base_app import configuration
from python_base_app import log_handling

DEFAULT_MIN_UID = 500
DEFAULT_MAX_UID = 65000
INVALID_SHELLS = ["/usr/sbin/nologin", "/bin/false"]

SYSTEM_EXCLUDE_USER_LIST = [
    'NextFreeUnixId'
]


class BaseUserHandlerConfigModel(configuration.ConfigModel):

    def __init__(self, p_section_name):
        super().__init__(p_section_name=p_section_name)
        self.min_uid = DEFAULT_MIN_UID
        self.max_uid = DEFAULT_MAX_UID

    def is_active(self):
        return self.admin_username is not None and self.admin_password is not None


class BaseUserHandler(object, metaclass=abc.ABCMeta):

    def __init__(self, p_config, p_exclude_user_list=None):

        self._logger = log_handling.get_logger(self.__class__.__name__)
        self._config = p_config
        self._exclude_user_list = p_exclude_user_list

        if self._exclude_user_list is None:
            self._exclude_user_list = []

    def is_valid_uid(self, p_uid, p_username=None, p_password=None, p_shell=None):
        if p_uid < self._config.min_uid  or p_uid > self._config.max_uid:
            return False

        if p_shell is not None:
            if p_shell in INVALID_SHELLS:
                return False

        if p_username is not None:
            if p_username in self._exclude_user_list or p_username in SYSTEM_EXCLUDE_USER_LIST:
                return False

        return True

    @abc.abstractmethod
    def list_users(self):  # pragma: no cover
        pass

    @abc.abstractmethod
    def get_uid(self, p_username):
        pass

    def authenticate(self, p_username, p_password):
        return False

    def is_admin(self, p_username):
        return False
