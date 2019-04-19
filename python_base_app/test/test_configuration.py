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

import unittest

from python_base_app import configuration
from python_base_app.test import base_test

SECTION_NAME = "MySection"
INT_VALUE = 123
BOOLEAN_VALUE = True


class SomeTestConfigModel(configuration.ConfigModel):

    def __init__(self):
        super(SomeTestConfigModel, self).__init__(p_section_name=SECTION_NAME)

        self.int = INT_VALUE
        self.none_int = configuration.NONE_INTEGER

        self.bool = BOOLEAN_VALUE
        self.none_bool = configuration.NONE_BOOLEAN


class TestConfiguration(base_test.BaseTestCase):

    def test_configuration_int(self):

        model = SomeTestConfigModel()

        self.assertEqual(model.get_option_type("none_int"), "int")
        self.assertIsNone(model.none_int)

        self.assertEqual(model.get_option_type("int"), "int")
        self.assertEqual(model.int, INT_VALUE)

    def test_configuration_boolean(self):

        model = SomeTestConfigModel()

        self.assertEqual(model.get_option_type("none_bool"), "bool")
        self.assertIsNone(model.none_bool)

        self.assertEqual(model.get_option_type("bool"), "bool")
        self.assertEqual(model.bool, BOOLEAN_VALUE)

    def test_configuration_unknown_option(self):

        model = SomeTestConfigModel()
        exception = None

        try:
            model.some_option

        except Exception as e:
            exception = e

        self.assertIsInstance(exception, AttributeError)

    def test_invalid_int(self):

        model = SomeTestConfigModel()

        config = configuration.Configuration()
        config.add_section(p_section=model)
        exception = None

        try:
            config.set_config_value(p_section_name=SECTION_NAME, p_option="int", p_option_value="hallo")

        except Exception as e:
            exception = e

        self.assertIsInstance(exception, configuration.ConfigurationException)
        self.assertIn("Invalid numerical value", str(exception))

    def test_invalid_none_int(self):

        model = SomeTestConfigModel()

        config = configuration.Configuration()
        config.add_section(p_section=model)
        exception = None

        try:
            config.set_config_value(p_section_name=SECTION_NAME, p_option="none_int", p_option_value="hallo")

        except Exception as e:
            exception = e

        self.assertIsInstance(exception, configuration.ConfigurationException)
        self.assertIn("Invalid numerical value", str(exception))

    def test_invalid_boolean(self):

        model = SomeTestConfigModel()

        config = configuration.Configuration()
        config.add_section(p_section=model)
        exception = None

        try:
            config.set_config_value(p_section_name=SECTION_NAME, p_option="bool", p_option_value="123")

        except Exception as e:
            exception = e

        self.assertIsInstance(exception, configuration.ConfigurationException)
        self.assertIn("Invalid Boolean value", str(exception))

    def test_invalid_none_boolean(self):

        model = SomeTestConfigModel()

        config = configuration.Configuration()
        config.add_section(p_section=model)
        exception = None

        try:
            config.set_config_value(p_section_name=SECTION_NAME, p_option="none_bool", p_option_value="123")

        except Exception as e:
            exception = e

        self.assertIsInstance(exception, configuration.ConfigurationException)
        self.assertIn("Invalid Boolean value", str(exception))

    def test_valid_boolean_values(self):

        model = SomeTestConfigModel()

        config = configuration.Configuration()
        config.add_section(p_section=model)

        for value in configuration.VALID_BOOLEAN_FALSE_VALUES:
            config.set_config_value(p_section_name=SECTION_NAME, p_option="bool", p_option_value=value)
            self.assertFalse(model.bool)

        for value in configuration.VALID_BOOLEAN_TRUE_VALUES:
            config.set_config_value(p_section_name=SECTION_NAME, p_option="bool", p_option_value=value)
            self.assertTrue(model.bool)


if __name__ == '__main__':
    unittest.main()
