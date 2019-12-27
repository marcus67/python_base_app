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
import os.path

from python_base_app import configuration
from python_base_app.test import base_test

SECTION_NAME = "MySection"
INT_VALUE = 123
NEW_INT_VALUE = 456
STRING_VALUE = "Hello"
BOOLEAN_VALUE = True


class SomeTestConfigModel(configuration.ConfigModel):

    def __init__(self):
        super(SomeTestConfigModel, self).__init__(p_section_name=SECTION_NAME)

        self.string = STRING_VALUE

        self.int = INT_VALUE
        self.none_int = configuration.NONE_INTEGER

        self.bool = BOOLEAN_VALUE
        self.none_bool = configuration.NONE_BOOLEAN
        
        self.empty_int_array = [configuration.NONE_INTEGER]
        self.int_array = [1, 2]

        self.empty_string_array = [configuration.NONE_STRING]
        self.string_array = ["somebody", "in", "there"]


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
        
        
    def test_valid_int_array(self):
        
        model = SomeTestConfigModel()

        self.assertIsNotNone(model.int_array)
        self.assertEqual(2, len(model.int_array))
        self.assertEqual(1, model.int_array[0])
        self.assertEqual(2, model.int_array[1])

    def test_valid_empty_int_array(self):

        model = SomeTestConfigModel()

        attr = model.none_int
        attr = model.empty_int_array
        self.assertIsNotNone(attr)
        self.assertEqual(0, len(attr))

    def test_valid_string_array(self):

        model = SomeTestConfigModel()

        self.assertIsNotNone(model.string_array)
        self.assertEqual(3, len(model.string_array))
        self.assertEqual("somebody", model.string_array[0])
        self.assertEqual("in", model.string_array[1])
        self.assertEqual("there", model.string_array[2])

    def test_valid_empty_string_array(self):

        model = SomeTestConfigModel()

        self.assertIsNotNone(model.empty_string_array)
        self.assertEqual(0, len(model.empty_string_array))

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


    def test_load_configuration(self):

        config = configuration.Configuration()
        model = SomeTestConfigModel()
        config.add_section(p_section=model)
        config_filename = os.path.join(self.get_test_data_path(), "test.config")
        config.read_config_file(p_filename=config_filename)

        self.assertEqual(234, model.int)
        self.assertEqual("There!", model.string)
        self.assertFalse(model.bool)

        self.assertEqual(len(model.int_array), 3)
        self.assertEqual(model.int_array[0], 1)
        self.assertEqual(model.int_array[1], 2)
        self.assertEqual(model.int_array[2], 3)

        self.assertEqual(len(model.empty_int_array), 3)
        self.assertEqual(model.empty_int_array[0], 4)
        self.assertEqual(model.empty_int_array[1], 5)
        self.assertEqual(model.empty_int_array[2], 6)

        self.assertEqual(len(model.string_array), 4)
        self.assertEqual(model.string_array[0], "somebody")
        self.assertEqual(model.string_array[1], "in")
        self.assertEqual(model.string_array[2], "there")
        self.assertEqual(model.string_array[3], "?")

        self.assertEqual(len(model.empty_string_array), 3)
        self.assertEqual(model.empty_string_array[0], "one")
        self.assertEqual(model.empty_string_array[1], "two")
        self.assertEqual(model.empty_string_array[2], "three")


    def test_override_by_command_line_options(self):

        config = configuration.Configuration()
        model = SomeTestConfigModel()
        config.add_section(p_section=model)

        self.assertEqual(model.int, INT_VALUE)

        parameters = [
            "{section}.int={value}".format(section=SECTION_NAME, value=NEW_INT_VALUE)
        ]

        config.read_command_line_parameters(parameters)

        self.assertEqual(model.int, NEW_INT_VALUE)

    def test_override_by_environment(self):

        config = configuration.Configuration()
        model = SomeTestConfigModel()
        config.add_section(p_section=model)

        self.assertEqual(model.int, INT_VALUE)

        environment = {
            "{section}__int".format(section=SECTION_NAME): str(NEW_INT_VALUE)
        }

        config.read_environment_parameters(p_environment_dict=environment)

        self.assertEqual(model.int, NEW_INT_VALUE)


if __name__ == '__main__':
    unittest.main()
