# -*- coding: utf-8 -*-
#    Copyright (C) 2019-2024  Marcus Rickert
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

import abc
import datetime

import jwt

from python_base_app import configuration, log_handling

SECTION_NAME = "TokenHandler"


class TokenException(Exception):
    pass


# Ideas taken from https://realpython.com/user-authentication-with-angular-4-and-flask/
class BaseTokenHandlerConfigModel(configuration.ConfigModel):

    def __init__(self, p_section_name=SECTION_NAME):
        super().__init__(p_section_name=p_section_name)

        self.algorithm = "HS256"
        self.max_token_age_in_days = 7
        self.token_life_in_minutes = 10
        self.refresh_token_life_in_minutes = 60 * 24
        self.token_cleanup_interval_in_hours = 1


class BaseTokenHandler:

    def __init__(self, p_config: BaseTokenHandlerConfigModel, p_secret_key: str):
        self._config = p_config
        self._secret_key = p_secret_key
        self._logger = log_handling.get_logger(self.__class__.__name__)

    def create_token(self, p_id: str, p_reference_time: datetime.datetime = None, p_is_refresh: bool = False) -> str:
        """

        :param p_id:
        :param p_reference_time:
        :param p_is_refresh:
        :return:
        """
        if p_reference_time is None:
            p_reference_time = datetime.datetime.utcnow()

        life_in_minutes = self._config.refresh_token_life_in_minutes \
            if p_is_refresh else self._config.token_life_in_minutes
        expiry_time = p_reference_time + datetime.timedelta(minutes=life_in_minutes)

        # See https://stackoverflow.com/questions/27726066/jwt-refresh-token-flow
        payload = {
            'exp': expiry_time,
            'iat': p_reference_time,
            'sub': p_id,
            'is_refresh': p_is_refresh
        }
        self._logger.debug(f"Created token (refresh:{p_is_refresh}) for {p_id} with "
                           f"{life_in_minutes} minutes lifetime until {expiry_time}")
        return jwt.encode(payload, self._secret_key, algorithm=self._config.algorithm)

    def delete_token(self, p_token: str, p_deletion_time: datetime.datetime = None):

        self._logger.info(f"Blacklisting token {p_token}.")
        self._store_blacklisted_token(p_token=p_token, p_deletion_time=p_deletion_time)

    def decode_auth_token(self, p_token, p_is_refresh: bool = False) -> str:
        """
        Validates the auth token
        :param p_token:
        :param p_is_refresh:
        :return: id that the token was created for
        """

        try:
            payload = jwt.decode(p_token, key=self._secret_key, algorithms=[self._config.algorithm])

            if payload["is_refresh"] != p_is_refresh:
                raise TokenException(f"Refresh type {payload['is_refresh']} not as expected ({p_is_refresh})!")

            is_blacklisted_token = self._is_token_blacklisted(p_token=p_token)

            if is_blacklisted_token:
                raise TokenException("Token is blacklisted. Login in again.")

        except jwt.ExpiredSignatureError:
            if p_is_refresh:
                raise TokenException("Signature expired. Please log in again.")
            else:
                raise TokenException("Signature expired. Please refresh token or log in again.")

        except jwt.InvalidTokenError:
            raise TokenException("Invalid token. Please log in again.")

        return payload['sub']

    def cleanup(self, p_reference_time: datetime.datetime = None) -> int:
        count = self._clean_out_tokens(p_reference_time=p_reference_time)
        self._logger.info(f"Removed {count} auth tokens...")
        return count

    @abc.abstractmethod
    def _store_blacklisted_token(self, p_token: str, p_deletion_time: datetime.datetime = None):
        pass

    @abc.abstractmethod
    def _is_token_blacklisted(self, p_token: str):
        pass

    @abc.abstractmethod
    def _clean_out_tokens(self, p_reference_time: datetime.datetime = None):
        pass
