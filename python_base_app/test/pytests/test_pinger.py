# -*- coding: utf-8 -*-

#    Copyright (C) 2021-2022  Marcus Rickert
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

import os

import pytest

from python_base_app.configuration import ConfigurationException
from python_base_app.pinger import Pinger, PingerConfigModel
from python_base_app.tools import is_mac_os


@pytest.fixture
def default_pinger():
    return Pinger(p_config=PingerConfigModel(), p_default_port=6666)


def test_is_valid_ping(default_pinger):
    assert default_pinger.is_valid_ping(p_host="web.de")
    assert default_pinger.is_valid_ping(p_host="web.de:1")
    assert default_pinger.is_valid_ping(p_host="web.de:65535")
    assert default_pinger.is_valid_ping(p_host="web.de,some.other.host")
    assert default_pinger.is_valid_ping(p_host="web.de:6666,some.other.host")
    assert default_pinger.is_valid_ping(p_host="web.de:6666,some.other.host,some.other.host")
    assert default_pinger.is_valid_ping(p_host="192.168.1.1")
    assert default_pinger.is_valid_ping(p_host="192.168.1.1:6666")


def test_is_invalid_ping(default_pinger):
    assert not default_pinger.is_valid_ping(p_host="some.weird.host")
    assert not default_pinger.is_valid_ping(p_host="web.de:0")
    assert not default_pinger.is_valid_ping(p_host="web.de:65536")
    assert not default_pinger.is_valid_ping(p_host="some.weird.host,some.other.host")
    assert not default_pinger.is_valid_ping(p_host="some.weird.host:6666,some.other.host")
    assert not default_pinger.is_valid_ping(p_host="some.weird.host:6666,some.other.host,some.other.host")
    assert not default_pinger.is_valid_ping(p_host="256.168.1.1")
    assert not default_pinger.is_valid_ping(p_host="256.168.1.1:6666")


@pytest.mark.skipif(os.getenv("NO_PING"), reason="no ping allowed")
def test_ping_localhost(default_pinger: Pinger):
    result = default_pinger.ping(p_host="localhost")
    assert result is not None
    value = float(result)

    if is_mac_os():
        assert value < 0.2

    else:
        assert value < 0.1


@pytest.mark.skipif(os.getenv("NO_PING"), reason="no ping allowed")
def test_ping_google_dns(default_pinger: Pinger):
    result = default_pinger.ping(p_host="8.8.8.8")
    assert result is not None
    value = float(result)
    assert value > 0.01
    assert value < 1000


@pytest.mark.skipif(os.getenv("NO_PING"), reason="no ping allowed")
def test_ping_non_existing_host(default_pinger: Pinger):
    with pytest.raises(ConfigurationException):
        default_pinger.ping(p_host="localhostx")
