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

class TimingResult(object):

    def __init__(self):

        self.duration = None

    def set_duration(self, p_duration):

        self.duration = p_duration

def test_timing_context():

    result = TimingResult()

    sum = 0

    with tools.TimingContext(p_result_handler=lambda duration: result.set_duration(p_duration=duration)):
        for i in range (0, 10):
            sum += i

    assert sum == 45
    assert result.duration is not None
    assert result.duration > 0
    assert result.duration < 0.1


def test_is_valid_dns_name():
    assert tools.is_valid_dns_name(p_dns_name="web.de")
    assert tools.is_valid_dns_name(p_dns_name="web.de:1")
    assert tools.is_valid_dns_name(p_dns_name="web.de:65535")
    assert tools.is_valid_dns_name(p_dns_name="192.168.1.1")
    assert tools.is_valid_dns_name(p_dns_name="192.168.1.1:6666")

def test_is_invalid_dns_name():
    assert not tools.is_valid_dns_name(p_dns_name="some.weird.host")
    assert not tools.is_valid_dns_name(p_dns_name="web.de:0")
    assert not tools.is_valid_dns_name(p_dns_name="web.de:65536")
    assert not tools.is_valid_dns_name(p_dns_name="256.168.1.1")
    assert not tools.is_valid_dns_name(p_dns_name="256.168.1.1:6666")

def test_split_host_url():
    assert tools.split_host_url("some.host", p_default_port_number=123) == ("some.host", 123)
    assert tools.split_host_url("some.host:345", p_default_port_number=123) == ("some.host", 345)
