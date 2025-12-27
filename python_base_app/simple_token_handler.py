# -*- coding: utf-8 -*-
import datetime

from python_base_app.base_token_handler import BaseTokenHandler, BaseTokenHandlerConfigModel


#    Copyright (C) 2019-2023  Marcus Rickert
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


class SimpleTokenHandler(BaseTokenHandler):

    def __init__(self, p_config: BaseTokenHandlerConfigModel, p_secret_key: str):
        super().__init__(p_config=p_config, p_secret_key=p_secret_key)

        self._token_store = {}

    def _store_blacklisted_token(self, p_token: str, p_deletion_time: datetime.datetime = None):

        if p_deletion_time is None:
            p_deletion_time = datetime.datetime.utcnow()

        self._token_store[p_token] = p_deletion_time

    def _is_token_blacklisted(self, p_token: str) -> bool:

        return p_token in self._token_store

    def _clean_out_tokens(self, p_reference_time: datetime.datetime = None):

        if p_reference_time is None:
            p_reference_time = datetime.datetime.utcnow()

        cutoff_time = p_reference_time + datetime.timedelta(days=-self._config.max_token_age_in_days)

        tokens_to_be_removed = [token for (token, creation_time) in self._token_store.items() if
                                creation_time < cutoff_time]

        for token in tokens_to_be_removed:
            del self._token_store[token]

        return len(tokens_to_be_removed)
