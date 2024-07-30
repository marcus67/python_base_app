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

import datetime
import os
import socket
import tempfile

import pytest

from python_base_app import configuration
from python_base_app import tools
from python_base_app.tools import RepetitiveObjectWriter, wrap_retry_until_expected_result

global missing_calls_counter


def test_anonymize_url():
    assert 'http://user:[HIDDEN]@some-host/some-url' == tools.anonymize_url(p_url='http://user:pwd@some-host/some-url')


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

    my_sum = 0

    with tools.TimingContext(p_result_handler=lambda duration: result.set_duration(p_duration=duration)):
        for i in range(0, 10):
            my_sum += i

    assert my_sum == 45
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


def test_today():
    today = tools.get_today()
    assert today.hour == 0
    assert today.minute == 0
    assert today.second == 0
    assert today.microsecond == 0


def test_running_in_docker():
    assert not tools.running_in_docker()


def test_running_in_snap():
    assert not tools.running_in_snap()


def test_get_ip_address_by_dns_name():
    assert tools.get_ip_address_by_dns_name("localhost") == "127.0.0.1"
    assert tools.get_ip_address_by_dns_name("111.111.111.111") == "111.111.111.111"
    with pytest.raises(socket.gaierror):
        tools.get_ip_address_by_dns_name("xyx.xyx.xyx")


def test_get_all_ip_address_by_dns_name():
    addresses = tools.get_ip_addresses_by_dns_name("localhost")
    assert len(addresses) == 1
    assert "127.0.0.1" in addresses

    addresses = tools.get_ip_addresses_by_dns_name("127.0.0.1")
    assert len(addresses) == 1
    assert "127.0.0.1" in addresses


def test_get_dns_name_by_ip_address():
    assert tools.get_dns_name_by_ip_address("127.0.0.1") == "localhost"
    assert tools.get_dns_name_by_ip_address("111.111.111.111") == "111.111.111.111"
    assert tools.get_dns_name_by_ip_address("0.0.0") == "0.0.0"


def test_repetitive_object_writer_one_file():
    with tempfile.TemporaryDirectory() as d:
        filename_pattern = os.path.join(d, "base.{type}.{index:04d}.json")
        writer = RepetitiveObjectWriter(p_base_filename_pattern=filename_pattern)
        writer.write_object(p_object="test")

        filename = os.path.join(d, "base.generic.0001.json")

        assert os.path.exists(filename)

        with open(filename, "r") as f:
            content = f.read()
            assert content == "test"


def test_repetitive_object_writer_two_files_ignore_same_objects_but_different():
    with tempfile.TemporaryDirectory() as d:
        filename_pattern = os.path.join(d, "base.{type}.{index:04d}.json")
        writer = RepetitiveObjectWriter(p_base_filename_pattern=filename_pattern)
        writer.write_object(p_object="test")
        writer.write_object(p_object="hallo")

        filename = os.path.join(d, "base.generic.0002.json")

        assert os.path.exists(filename)

        with open(filename, "r") as f:
            content = f.read()
            assert content == "hallo"


def test_repetitive_object_writer_two_files_ignore_same_objects_but_same():
    with tempfile.TemporaryDirectory() as d:
        filename_pattern = os.path.join(d, "base.{type}.{index:04d}.json")
        writer = RepetitiveObjectWriter(p_base_filename_pattern=filename_pattern)
        writer.write_object(p_object="test")
        writer.write_object(p_object="test")

        filename = os.path.join(d, "base.generic.0002.json")

        assert not os.path.exists(filename)


def test_repetitive_object_writer_two_files_not_ignore_same_objects():
    with tempfile.TemporaryDirectory() as d:
        filename_pattern = os.path.join(d, "base.{type}.{index:04d}.json")
        writer = RepetitiveObjectWriter(p_base_filename_pattern=filename_pattern, p_ignore_same_object=False)
        writer.write_object(p_object="test")
        writer.write_object(p_object="test")

        filename = os.path.join(d, "base.generic.0002.json")

        assert os.path.exists(filename)

        with open(filename, "r") as f:
            content = f.read()
            assert content == "test"


def test_repetitive_object_writer_one_file_with_type():
    with tempfile.TemporaryDirectory() as d:
        filename_pattern = os.path.join(d, "base.{type}.{index:04d}.json")
        writer = RepetitiveObjectWriter(p_base_filename_pattern=filename_pattern)
        writer.write_object(p_object="test", p_object_type="some-type")

        filename = os.path.join(d, "base.some-type.0001.json")

        assert os.path.exists(filename)

        with open(filename, "r") as f:
            content = f.read()
            assert content == "test"


def test_repetitive_object_writer_one_file_with_dict():
    with tempfile.TemporaryDirectory() as d:
        filename_pattern = os.path.join(d, "base.{type}.{index:04d}.json")
        writer = RepetitiveObjectWriter(p_base_filename_pattern=filename_pattern)
        writer.write_object(p_object={
            "some_key": "some text"
        })

        filename = os.path.join(d, "base.generic.0001.json")

        assert os.path.exists(filename)

        with open(filename, "r") as f:
            content = f.read()
            assert content == '{"some_key": "some text"}'


def repeat_me() -> str | None:
    global missing_calls_counter

    if missing_calls_counter == 0:
        return "OK"

    missing_calls_counter -= 1

    return None


def test_wrap_wrap_retry_until_non_none_sufficient_retries():
    global missing_calls_counter

    missing_calls_counter = 1

    wrapped_function = wrap_retry_until_expected_result(func=repeat_me, p_max_retries=1)

    result = wrapped_function()

    assert result is not None
    assert "OK" == result


def test_wrap_wrap_retry_until_non_none_insufficient_retries():
    global missing_calls_counter

    missing_calls_counter = 2

    wrapped_function = wrap_retry_until_expected_result(func=repeat_me, p_max_retries=1)

    with pytest.raises(AssertionError) as e:
        result = wrapped_function()

    assert "did not return expected result" in str(e)


def test_wrap_wrap_retry_until_non_none_wait_time_one_retry():
    global missing_calls_counter

    missing_calls_counter = 1

    wrapped_function = wrap_retry_until_expected_result(func=repeat_me, p_max_retries=1, p_wait_time=1)

    start_time = datetime.datetime.now()
    result = wrapped_function()
    end_time = datetime.datetime.now()

    assert result is not None
    assert "OK" == result

    exec_time_in_seconds = (end_time - start_time).total_seconds()

    assert exec_time_in_seconds >= 1
    assert exec_time_in_seconds < 1.1


def test_wrap_wrap_retry_until_non_none_wait_time_three_retries():
    global missing_calls_counter

    missing_calls_counter = 3

    wrapped_function = wrap_retry_until_expected_result(func=repeat_me, p_max_retries=4, p_wait_time=1)

    start_time = datetime.datetime.now()
    result = wrapped_function()
    end_time = datetime.datetime.now()

    assert result is not None
    assert "OK" == result

    exec_time_in_seconds = (end_time - start_time).total_seconds()

    assert exec_time_in_seconds >= 3
    assert exec_time_in_seconds < 3.1


def test_wrap_wrap_retry_until_non_none_wait_time_three_retries_exceeded():
    global missing_calls_counter

    missing_calls_counter = 4

    wrapped_function = wrap_retry_until_expected_result(func=repeat_me, p_max_retries=3, p_wait_time=1)

    start_time = datetime.datetime.now()

    with pytest.raises(AssertionError) as e:
        result = wrapped_function()

    assert "did not return expected result" in str(e)

    end_time = datetime.datetime.now()

    exec_time_in_seconds = (end_time - start_time).total_seconds()

    assert exec_time_in_seconds >= 3
    assert exec_time_in_seconds < 3.1
