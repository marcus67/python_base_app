# -*- coding: utf-8 -*-
import socket

from python_base_app.net_tools import is_port_available
from python_base_app.test.base_test import BaseTestCase


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

def test_is_port_available_true():
    port = BaseTestCase.get_status_server_port()
    assert is_port_available(p_port=int(port))


def test_is_port_available_false():
    port = BaseTestCase.get_status_server_port()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", int(port)))
        s.listen()

        assert not is_port_available(p_port=int(port))

