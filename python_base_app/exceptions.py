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

class InstallationException(Exception):
    pass


class SignalHangUp(Exception):
    pass


class ScriptExecutionError(Exception):

    def __init__(self, p_script_name, p_exit_code):
        super().__init__()
        self.script_name = p_script_name
        self.exit_code = p_exit_code


class ArtifactNotFoundException(Exception):

    def __init__(self, p_artifact_path, p_error_code, p_result_document=None):
        self._artifact_path = p_artifact_path
        self._error_code = p_error_code
        self._result_document = p_result_document

    def __str__(self):
        return "ArtifactNotFoundException with error code '%s' while accessing artifact '%s'" % (
            str(self._error_code), self._artifact_path)

    @property
    def result_document(self):
        return self._result_document


class ArtifactBlockedException(Exception):

    def __init__(self, p_artifact_path, p_error_code):
        self._artifact_path = p_artifact_path
        self._error_code = p_error_code

    def __str__(self):
        return "ArtifactBlockedException with error code '%s' while accessing artifact '%s'" % (
            str(self._error_code), self._artifact_path)

class RangeNotSatisfiableException(Exception):

    def __init__(self, p_artifact_path, p_error_code):
        self._artifact_path = p_artifact_path
        self._error_code = p_error_code

    def __str__(self):
        return "RangeNotSatisfiableException with error code '%s' while accessing artifact '%s'" % (
            str(self._error_code), self._artifact_path)


class TimeoutException(Exception):

    def __init__(self, p_artifact_path, p_error_code):
        self._artifact_path = p_artifact_path
        self._error_code = p_error_code

    def __str__(self):
        return "TimeOutException with error code '%s' while accessing artifact '%s'" % (
            str(self._error_code), self._artifact_path)


class UnauthorizedException(Exception):

    def __init__(self, p_artifact_path, p_login, p_error_code):
        self._artifact_path = p_artifact_path
        self._login = p_login
        self._error_code = p_error_code

    def __str__(self):
        return "UnauthorizedException with error code '%s' while accessing artifact '%s' using login '%s'" % (
            str(self._error_code), self._artifact_path, self._login)


class DuplicateKeyException(Exception):

    def __init__(self, p_key, p_error_code):
        self._key = p_key
        self._error_code = p_error_code

    def __str__(self):
        return "DuplicateKeyException with error '%s' for key '%s'" % (
            str(self._error_code), str(self._key))
