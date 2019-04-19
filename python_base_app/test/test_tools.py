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

import datetime

import pytest

from python_base_app import configuration
from python_base_app import tools


def test_anonymize_url():
    assert 'http://user:[HIDDEN]@somehost/someurl' == tools.anonymize_url(p_url='http://user:pwd@somehost/someurl')


def test_get_string_as_time_valid_time():
    assert datetime.time(12, 0, 0) == tools.get_string_as_time(p_string="12")
    assert datetime.time(12, 23, 0) == tools.get_string_as_time(p_string="12:23")
    assert datetime.time(12, 23, 45) == tools.get_string_as_time(p_string="12:23:45")


def test_get_string_as_time_invalid_time():
    with pytest.raises(configuration.ConfigurationException):
        tools.get_string_as_time(p_string="12A:23 45")

    with pytest.raises(configuration.ConfigurationException):
        tools.get_string_as_time(p_string="12:23 45")

    with pytest.raises(configuration.ConfigurationException):
        tools.get_string_as_time(p_string="X")


def test_get_string_as_time_empty_string():
    assert tools.get_string_as_time(p_string="") is None


def test_get_string_as_time_none():
    assert tools.get_string_as_time(p_string=None) is None


def test_get_string_as_duration_valid_time():
    assert 12 * 60 * 60 == tools.get_string_as_duration(p_string="12h")
    assert 12 * 60 * 60 + 23 * 60 == tools.get_string_as_duration(p_string="12h23m")
    assert 12 * 60 * 60 + 23 * 60 + 45 == tools.get_string_as_duration(p_string="12h23m45s")


def test_get_string_as_duration_invalid_time():
    with pytest.raises(configuration.ConfigurationException):
        tools.get_string_as_duration(p_string="12x")

    with pytest.raises(configuration.ConfigurationException):
        tools.get_string_as_duration(p_string="12h23")

    with pytest.raises(configuration.ConfigurationException):
        tools.get_string_as_duration(p_string="X")


def test_get_string_as_duration_empty_string():
    assert tools.get_string_as_duration(p_string="") is None


def test_get_string_as_duration_none():
    assert tools.get_string_as_duration(p_string=None) is None
