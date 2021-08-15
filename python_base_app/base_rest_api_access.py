# -*- coding: utf-8 -*-

#    Copyright (C) 2019  Marcus Rickert
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

import json
import logging
from os.path import join

import requests

from python_base_app import configuration
from python_base_app import exceptions
from python_base_app import log_handling
from python_base_app import tools


class BaseRestAPIAccessConfigModel(configuration.ConfigModel):

    def __init__(self, p_section_name):
        super(BaseRestAPIAccessConfigModel, self).__init__(p_section_name)

        self.host_url = configuration.NONE_STRING

        self.login = configuration.NONE_STRING
        self.password = configuration.NONE_STRING
        self.access_token = configuration.NONE_STRING
        self.admin_login = configuration.NONE_STRING
        self.admin_password = configuration.NONE_STRING

    def is_active(self):
        return self.host_url is not None


class BaseRestAPIAccess(object):

    def __init__(self, p_config, p_section_name, p_base_api_url=""):

        self._config = p_config
        self._logger = log_handling.get_logger(p_section_name)

        # logger = log_handling.get_logger("requests.packages.urllib3.connectionpool")
        logger = log_handling.get_logger("urllib3.connectionpool")
        logger.setLevel(logging.WARNING)

        self._api_base_url = p_base_api_url

    def _get_api_url(self, p_command=None):

        if p_command is not None:
            return self._config.host_url + join(self._api_base_url, p_command)

        else:
            return self._config.host_url + self._api_base_url

    def _handle_runtime_exception(self, p_status_code, p_exception, p_artifact_path='UNKNOWN', p_login='UNKOWN',
                                  p_result_document=None, p_key=None):

        error_code = p_status_code
        error_message = None

        if p_artifact_path is not None:
            p_artifact_path = tools.anonymize_url(p_artifact_path)

        if error_code is None:
            try:
                error_json = json.loads(str(p_result_document))
                error_code = int(error_json['errors'][0]['status'])
                error_message = error_json['errors'][0]['message']

            except Exception:
                pass

        if error_code is None:
            try:
                error_json = json.loads(str(p_exception))
                error_code = int(error_json['errors'][0]['status'])
                error_message = error_json['errors'][0]['message']

            except Exception:
                pass

        if error_code is None:
            try:
                error_code = int(str(p_exception))

            except Exception:
                pass

        # print("error_message", error_message)

        if p_result_document is not None:
            fmt = "Result document: %s" % p_result_document
            self._logger.info(fmt)

        if error_code == 400 and error_message is not None and "key already exists" in error_message:

            fmt = "Objekt with key '%s' already exists" % p_key
            self._logger.error(fmt)
            raise exceptions.DuplicateKeyException(p_key=p_key, p_error_code=error_code)

        elif error_code == 401:

            if p_login is None:
                fmt = "Access to '{artifact_path}' was not authorized"

            else:
                fmt = "Access to '{artifact_path}' using login '{p_login}' was not authorized"

            self._logger.error(fmt.format(artifact_path=p_artifact_path, login=p_login))
            raise exceptions.UnauthorizedException(p_artifact_path=p_artifact_path, p_login=p_login,
                                                   p_error_code=error_code)

        elif error_code == 403:

            fmt = "Access to '%s' using login '%s' was not successful (too many attempts)" % (p_artifact_path, p_login)
            self._logger.error(fmt)
            raise exceptions.UnauthorizedException(p_artifact_path=p_artifact_path, p_login=p_login,
                                                   p_error_code=error_code)

        elif error_code == 404:

            fmt = "Artifact '%s' not found" % p_artifact_path
            self._logger.error(fmt)
            raise exceptions.ArtifactNotFoundException(p_artifact_path=p_artifact_path, p_error_code=error_code,
                                                       p_result_document=p_result_document)

        elif error_code == 416:

            fmt = "Range not satisfiable in '%s'" % p_artifact_path
            self._logger.error(fmt)
            raise exceptions.RangeNotSatisfiableException(p_artifact_path=p_artifact_path, p_error_code=error_code)

        elif error_code == 500 or error_code == 423:

            fmt = "Artifact '%s' is locked" % p_artifact_path
            self._logger.error(fmt)
            raise exceptions.ArtifactBlockedException(p_artifact_path=p_artifact_path, p_error_code=error_code)

        elif error_code == 504:

            fmt = "Timeout while accessing artifact '%s'" % p_artifact_path
            self._logger.error(fmt)
            raise exceptions.TimeoutException(p_artifact_path=p_artifact_path, p_error_code=error_code)

        else:

            fmt = "Unknown error code '%s' with message '%s' while accessing artifact '%s'" % (
                error_code, error_message, p_artifact_path)
            self._logger.error(fmt)

            if p_result_document is not None:
                fmt = "Result document: %s" % p_result_document
                self._logger.info(fmt)

            raise p_exception

    def _get_auth(self, p_requires_admin=False):
        if p_requires_admin:
            return tuple(self._config.admin_login, self._config.admin_password)

        else:
            return tuple(self._config.login, self._config.password)

    def execute_api_call(self, p_url, p_requires_authorization=False,
                         p_requires_admin=False,
                         p_mime_type=None,
                         p_method="GET",
                         p_data=None,
                         p_parameters=None,
                         p_jsonify=False):

        result = None
        headers = {}
        login = None
        r = None

        try:

            if p_requires_authorization:
                auth = self._get_auth(p_requires_admin)
                login = auth[0]

            else:
                auth = None

            if p_mime_type:
                headers['Content-type'] = p_mime_type

            fmt = "Executing %s API call '%s'" % (p_method, tools.anonymize_url(p_url))
            self._logger.debug(fmt)

            if p_method == "GET":
                r = requests.get(p_url, auth=auth, stream=False, headers=headers, params=p_parameters)

            elif p_method == "PUT":
                r = requests.put(p_url, auth=auth, data=p_data, headers=headers, params=p_parameters)

            elif p_method == "POST":
                r = requests.post(p_url, auth=auth, data=p_data, headers=headers, params=p_parameters)

            elif p_method == "DELETE":
                r = requests.delete(p_url, auth=auth, data=p_data, headers=headers, params=p_parameters)

            else:
                raise NotImplementedError("Invalid method '%s'" % p_method)

            try:
                if p_jsonify:
                    result = json.loads(r.content.decode("UTF-8"))

                else:
                    result = r.content.decode("UTF-8")
                # print ("result", result)

            except Exception:
                pass

            r.raise_for_status()

            r.close()


        except Exception as e:

            self._handle_runtime_exception(
                p_status_code=r.status_code if r is not None else None,
                p_exception=e,
                p_artifact_path=tools.anonymize_url(p_url),
                p_key=tools.anonymize_url(p_url),
                p_result_document=result,
                p_login=login)

        return result
