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

import abc
import configparser
import re

from python_base_app import log_handling
from python_base_app import tools

REGEX_CMDLINE_PARAMETER = re.compile(r"([-a-zA-Z_0-9]+)\.([a-zA-Z_0-9]+)=(.*)")
REGEX_ENV_PARAMETER = re.compile("([a-zA-Z_0-9]+)__([a-zA-Z_0-9]+)")

NONE_BOOLEAN = type(True)
NONE_INTEGER = type(1)
NONE_STRING = type("X")

OPTION_ARRAY_PATTERN = re.compile(r"([^[]*)\[([0-9]+)\]")

VALID_BOOLEAN_TRUE_VALUES = ['1', 'TRUE', 'T', 'YES', 'WAHR', 'JA', 'J']
VALID_BOOLEAN_FALSE_VALUES = ['0', 'FALSE', 'F', 'NO', 'FALSCH', 'NEIN', 'N']

IGNORED_DICT_KEYS = [
    'section_name',
    '_options'
]

class ConfigurationException(Exception):

    def __init__(self, p_text):
        super(ConfigurationException, self).__init__(p_text)


class ConfigurationSectionHandler(object, metaclass=abc.ABCMeta):

    def __init__(self, p_section_prefix):
        self._section_prefix = p_section_prefix
        self._configuration = None
        self._logger = log_handling.get_logger(self.__class__.__name__)

    @property
    def section_prefix(self):
        return self._section_prefix

    @abc.abstractmethod
    def handle_section(self, p_section_name):
        pass

    def set_configuration(self, p_configuration):
        self._configuration = p_configuration

    def scan(self, p_section):
        self._configuration.add_section(p_section=p_section)
        self._configuration.scan_section(p_section_name=p_section.section_name)


NONE_TYPE_PREFIX = "_TYPE_"
NONE_ARRAY_TYPE_PREFIX = "_ARRAY_TYPE_"


class SimpleConfigurationSectionHandler(ConfigurationSectionHandler):

    def __init__(self, p_config_model):
        super().__init__(p_section_prefix=p_config_model._section_name)
        self._config_model = p_config_model

    def handle_section(self, p_section_name):
        self.scan(p_section=self._config_model)


class ConfigModel(object):

    def __init__(self, p_section_name, p_class_name=None):

        self.section_name = p_section_name
        self._options = {}

    def is_active(self):
        raise NotImplementedError("ConfigModel.is_active")

    def get_option_type(self, p_option_name):

        p_effective_name = NONE_ARRAY_TYPE_PREFIX + p_option_name

        value = self.__dict__.get(p_effective_name)

        if value is not None:
            return "list_" + value.__name__

        else:
            p_effective_name = NONE_TYPE_PREFIX + p_option_name

            value = self.__dict__.get(p_effective_name)

            if value is not None:
                return value.__name__

            else:
                value = self.__dict__[p_option_name]

                if isinstance(value, list):
                    if len(value) == 0:
                        fmt = "Option '{option}' defines empty array without type"
                        raise ConfigurationException(fmt.format(option=p_option_name))

                    return "list_" + type(value[0]).__name__

                else:
                    return type(value).__name__

    def has_option(self, p_option_name):

        p_effective_name = NONE_TYPE_PREFIX + p_option_name
        p_effective_name_list = NONE_ARRAY_TYPE_PREFIX + p_option_name

        return p_option_name in self.__dict__ or \
               p_effective_name in self.__dict__ or p_effective_name_list in self.__dict__

    def __getattr__(self, p_option_name):

        # Note: __getattr__ is ONLY called if the builtin mechanism did not find the attribute, that is
        # for all existing attributes the method WILL NEVER BE CALLED!

        p_effective_name = NONE_TYPE_PREFIX + p_option_name
        value = self.__dict__.get(p_effective_name)

        if value is not None:
            return None

        else:
            p_effective_name = NONE_ARRAY_TYPE_PREFIX + p_option_name
            value = self.__dict__.get(p_effective_name)

            if value is not None:
                return []

            else:
                fmt = "unknown option name '{name}' in section '[{section}]'"
                raise AttributeError(fmt.format(name=p_option_name, section=self.__dict__.get("section_name")))

    def __setattr__(self, p_option_name, p_value):

        if isinstance(p_value, list):
            if len(p_value) == 1 and isinstance(p_value[0], type):
                p_effective_name = NONE_ARRAY_TYPE_PREFIX + p_option_name
                self.__dict__[p_effective_name] = p_value[0]

            else:
                self.__dict__[p_option_name] = p_value

        elif isinstance(p_value, type):
            p_effective_name = NONE_TYPE_PREFIX + p_option_name
            self.__dict__[p_effective_name] = p_value

        else:
            self.__dict__[p_option_name] = p_value

    def post_process(self):

        pass


class Configuration(object):

    def __init__(self):

        #super().__init__(p_section_name="_Configuration_")

        self._sections = {}
        self._logger = log_handling.get_logger(self.__class__.__name__)
        self._section_handlers = []
        self.config = configparser.ConfigParser(strict=False)

    def add_section(self, p_section):

        if p_section.section_name in self._sections:
            fmt = "Overwriting existing section '%s'" % p_section.section_name
            self._logger.warning(fmt)

        self._sections[p_section.section_name] = p_section

    def register_section_handler(self, p_section_handler):

        self._section_handlers.append(p_section_handler)
        p_section_handler.set_configuration(p_configuration=self)

    def __getitem__(self, p_key):

        if p_key not in self._sections:
            raise ConfigurationException("No section '%s' configured in class %s" % (p_key, self.__class__.__name__))

        return self._sections[p_key]

    def set_config_value(self, p_section_name, p_option, p_option_value):

        section = self._sections.get(p_section_name)
        append_to_list = False

        if section is None:
            raise ConfigurationException("Invalid section name '%s'" % p_section_name)

        match = OPTION_ARRAY_PATTERN.match(p_option)

        if match is not None:
            if int(match.group(2)) > 0:
                append_to_list = True
            p_option = match.group(1)

        if not section.has_option(p_option_name=p_option):
            raise ConfigurationException(
                "Configuration file contains invalid setting '%s' in section '%s'" % (p_option, p_section_name))

        option_type = section.get_option_type(p_option_name=p_option)
        upper_value = p_option_value.upper()

        if 'bool' in option_type:
            if upper_value in VALID_BOOLEAN_TRUE_VALUES:
                value = True

            elif upper_value in VALID_BOOLEAN_FALSE_VALUES:
                value = False

            else:
                raise ConfigurationException("Invalid Boolean value '%s' in setting '%s' of section '%s'" % (
                    p_option_value, p_option, p_section_name))

        elif 'int' in option_type:
            try:
                value = int(p_option_value)

            except Exception as e:
                raise ConfigurationException("Invalid numerical value '%s' in setting '%s' of section '%s': %s" % (
                    p_option_value, p_option, p_section_name, str(e)))

        else:
            value = p_option_value

        if 'list' in option_type:
            if append_to_list:
                getattr(section, p_option).append(value)

            else:
                setattr(section, p_option, [value])

        else:
            setattr(section, p_option, value)

    def scan_section(self, p_section_name):

        section = self._sections.get(p_section_name)

        fmt = "Scanning settings for section '%s'" % p_section_name
        self._logger.debug(fmt)

        if section is None:
            raise ConfigurationException("Invalid section name '%s'" % p_section_name)

        for option in self.config.options(p_section_name):
            option_value = self.config.get(p_section_name, option)
            self.set_config_value(
                p_section_name=p_section_name,
                p_option=option,
                p_option_value=option_value)

    def handle_section(self, p_section_name, p_ignore_invalid_sections=False, p_warn_about_invalid_sections=False):

        for section_handler in self._section_handlers:
            if p_section_name.startswith(section_handler.section_prefix):
                section_handler.handle_section(p_section_name=p_section_name)
                return

        if p_ignore_invalid_sections:
            if p_warn_about_invalid_sections:
                fmt = "Ignoring invalid section '%s' (not all sections registered?)" % p_section_name
                self._logger.warning(fmt)

        else:
            fmt = "Invalid section '%s'" % p_section_name
            self._logger.error(fmt)
            raise ConfigurationException("Configuration file contains invalid section '%s'" % p_section_name)

    def read_config_file(self, p_filename=None, p_config_string=None,
                         p_ignore_invalid_sections=False, p_warn_about_invalid_sections=False):

        errorMessage = None

        if p_filename is not None:
            fmt = "Reading configuration file from '%s'" % p_filename
            self._logger.info(fmt)

            self.config.optionxform = str  # make options case sensitive

            try:
                filesRead = self.config.read([p_filename], encoding="UTF-8")

                if len(filesRead) != 1:
                    fmt = "Error while reading configuration file '{filename}' (file probably does not exist)"
                    errorMessage = fmt.format(filename=p_filename)

            except Exception as e:
                fmt = "Exception '{msg}' while reading configuration file '{filename}'"
                errorMessage = fmt.format(msg=str(e), filename=p_filename)

        if p_config_string is not None:

            try:
                self.config.read_string(p_config_string)

            except Exception as e:
                fmt = "Exception '{msg}' while reading setting"
                errorMessage = fmt.format(msg=str(e))

        if errorMessage is not None:
            raise ConfigurationException(errorMessage)

        for section_name in self.config.sections():
            if section_name in self._sections:

                new_section = self._sections[section_name]
                setattr(self, section_name, new_section)
                self.scan_section(section_name)

            else:

                self.handle_section(p_section_name=section_name,
                                    p_ignore_invalid_sections=p_ignore_invalid_sections,
                                    p_warn_about_invalid_sections=p_warn_about_invalid_sections)

    def write_to_file(self, p_filename):
        with open(p_filename, 'w') as configfile:
            first = True

            for section_name, config in self._sections.items():
                if first:
                    first = False

                else:
                    configfile.write("\n")

                configfile.write("[{name}]\n".format(name=section_name))

                for key, value in config.__dict__.items():
                    if key in IGNORED_DICT_KEYS:
                        continue

                    if key.startswith(NONE_TYPE_PREFIX) or key.startswith(NONE_ARRAY_TYPE_PREFIX):
                        continue

                    configfile.write("{key}={value}\n".format(key=key, value=value))

    def read_command_line_parameters(self, p_parameters):

        for par in p_parameters:
            result = REGEX_CMDLINE_PARAMETER.match(par)

            if result:

                section_name = result.group(1)
                option_name = result.group(2)
                value = result.group(3)

                protected_value = tools.protect_password_value(p_name=option_name, p_value=value)

                fmt = "Command line setting: set '[%s]%s' to value '%s'" % (
                    section_name, option_name, protected_value)
                self._logger.info(fmt)

                self.set_config_value(
                    p_section_name=section_name,
                    p_option=option_name,
                    p_option_value=value)

            else:
                fmt = "Incorrectly formatted command line setting: %s" % par
                self._logger.warning(fmt)

    def read_environment_parameters(self, p_environment_dict):

        for (name, value) in dict(p_environment_dict).items():
            result = REGEX_ENV_PARAMETER.match(name)

            if result:
                section_name = result.group(1)
                option_name = result.group(2)

                protected_value = tools.protect_password_value(p_name=option_name, p_value=value)

                fmt = "Environment setting: set '[{section_name}]{option_name}' to value '{value}'"
                self._logger.info(fmt.format(section_name=section_name, option_name=option_name, value=protected_value))

                self.set_config_value(
                    p_section_name=section_name,
                    p_option=option_name,
                    p_option_value=value)
