# -*- coding: utf-8 -*-

#    Copyright (C) 2021  Marcus Rickert
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

import pytest

from python_base_app import pinger

@pytest.fixture
def default_pinger():
    return pinger.Pinger(p_config=pinger.PingerConfigModel(), p_default_port=6666)

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

