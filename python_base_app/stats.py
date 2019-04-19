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

class MovingAverage(object):

    def __init__(self, p_sample_size):

        self._sample_size = p_sample_size
        self._pointer = 0
        self._values = []
        self._sum = 0.0

    def add_value(self, p_value):

        if len(self._values) < self._sample_size:
            self._values.append(p_value)

        else:
            self._sum = self._sum - self._values[self._pointer]
            self._values[self._pointer] = p_value
            self._pointer = self._pointer + 1
            if self._pointer == self._sample_size:
                self._pointer = 0

        self._sum = self._sum + p_value

    def get_value(self, p_default=None):

        if len(self._values) == 0:
            return p_default

        else:
            return 1.0 * self._sum / len(self._values)
