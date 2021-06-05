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

import inspect
import logging
import os
import sys
import unittest
from os.path import join, dirname

import pytest

from python_base_app import configuration
from python_base_app import log_handling

PARAMETER_NAME_CONFIGURATION_FILE = 'p_config_filename'
PARAMETER_NAME_TEST_DATA_BASE_DIR = 'p_test_data_base_dir'

DEFAULT_CONFIG_FILENAME = 'test.config'
DEFAULT_RESOURCE_REL_PATH = 'resources'

global g_capability_checkers

g_capability_checkers = {}


def register_capability_checkers(p_checkers):
    global g_capability_checkers

    g_capability_checkers.update(p_checkers)


class skip_if_env(object):

    def __init__(self, *p_env_names):

        if isinstance(p_env_names, list):
            self._env_names = p_env_names

        else:
            self._env_names = list(p_env_names)

    def __call__(self, f):

        def wrapped_f(*args):

            for env_name in self._env_names:
                if env_name in os.environ:
                    fmt = "Found {} in environment"
                    raise unittest.SkipTest(fmt.format(env_name))

            f(*args)

        return wrapped_f


class must_be_available(object):

    def __init__(self, p_required_capabilities):
        self._required_capabilities = p_required_capabilities
        self._logger = log_handling.get_logger(self.__class__.__name__)

    def __call__(self, f):

        def wrapped_f(*args):

            global g_capability_checkers

            missing_capabilities = []

            for cap in self._required_capabilities:
                if cap not in g_capability_checkers:
                    msg = "Capability '{cap}' has not been configured -> will be ignored"
                    self._logger.warn(msg.format(cap=cap))

                else:
                    checker = g_capability_checkers[cap]
                    if not checker():
                        missing_capabilities.append(cap)

            if len(missing_capabilities) > 0:
                fmt = "Missing capabilities: {caps}"
                msg = fmt.format(caps=", ".join(missing_capabilities))
                self._logger.info(msg)
                raise unittest.SkipTest(msg)

            f(*args)

        return wrapped_f


def add_tests_in_test_unit(
        p_test_suite, p_test_unit_class,
        p_config_filename=DEFAULT_CONFIG_FILENAME, p_test_data_base_dir=DEFAULT_RESOURCE_REL_PATH):
    for test_name in unittest.getTestCaseNames(p_test_unit_class, prefix="test"):
        test = p_test_unit_class(
            test_name,
            p_config_filename=p_config_filename,
            p_test_data_base_dir=p_test_data_base_dir)

        p_test_suite.addTest(test)


def get_config_filename():
    if len(sys.argv) > 1:
        return sys.argv[1]

    else:
        return None


def run_test_suite(p_test_suite):
    test_result = unittest.TextTestRunner(verbosity=2).run(p_test_suite)

    for (tc, reason) in test_result.skipped:
        print("SKIPPED: '%s'  REASON: '%s'" % (str(tc), reason))

    for (tc, reason) in test_result.errors:
        print("RUNTIME-ERROR: '%s'  REASON: '%s'" % (str(tc), reason))

    for (tc, reason) in test_result.failures:
        print("FAILED: '%s'  REASON: '%s'" % (str(tc), reason))

    if len(test_result.errors) > 0 or len(test_result.failures) > 0:
        exit(1)

    else:
        exit(0)


class BaseTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        base_dir = dirname(inspect.getfile(self.__class__))

        if PARAMETER_NAME_CONFIGURATION_FILE in kwargs:

            filename = kwargs.get(PARAMETER_NAME_CONFIGURATION_FILE, DEFAULT_CONFIG_FILENAME)

            if filename is None:
                filename = DEFAULT_CONFIG_FILENAME

            self._config_filename = join(base_dir, filename)
            del (kwargs[PARAMETER_NAME_CONFIGURATION_FILE])

        else:
            self._config_filename = join(base_dir, DEFAULT_CONFIG_FILENAME)

        if PARAMETER_NAME_TEST_DATA_BASE_DIR in kwargs:
            self._test_data_base_dir = join(base_dir, kwargs.get(PARAMETER_NAME_TEST_DATA_BASE_DIR))
            del (kwargs[PARAMETER_NAME_TEST_DATA_BASE_DIR])

        else:
            self._test_data_base_dir = join(base_dir, DEFAULT_RESOURCE_REL_PATH)

        super(BaseTestCase, self).__init__(*args, **kwargs)

        log_handling.start_logging(p_use_filter=False)
        self._config = self.configuration_factory()
        self._logger = log_handling.get_logger(self.__class__.__name__)

    @classmethod
    def setUpClass(cls):
        logger = log_handling.get_logger("urllib3.connectionpool")
        logger.setLevel(logging.WARNING)

    def configuration_factory(self):
        return configuration.Configuration()

    def add_config_section(self, p_section):

        self._config.add_section(p_section=p_section)

    def load_configuration(self):

        if self._config_filename is None:
            msg = "No filename specified for test case '{testcase}'"
            raise configuration.ConfigurationException(msg.format(testcase=self.__class__.__name__))

        self._config.read_config_file(self._config_filename,
                                      p_ignore_invalid_sections=True)

    def get_test_data_path(self, p_rel_path='.'):

        if self._test_data_base_dir is None:
            msg = "No base path specified for test case '{testcase}'"
            raise configuration.ConfigurationException(msg.format(testcase=self.__class__.__name__))

        return join(self._test_data_base_dir, p_rel_path)

    def execute_pytest(self, p_base_dir=None, p_rel_path="pytest"):

        if p_base_dir is None:
            p_base_dir = os.path.dirname(__file__)

        pytest_dir = os.path.join(p_base_dir, p_rel_path)

        fmt = "Executing pytest tests in directory {dirname}"
        self._logger.info(fmt.format(dirname=pytest_dir))

        pytest_result = pytest.cmdline.main([pytest_dir])

        self.assertEqual(pytest_result, 0)

    def check_list_length(self, p_list, p_length):

        self.assertIsNotNone(p_list)
        self.assertEqual(len(p_list), p_length)
