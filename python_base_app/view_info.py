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

from python_base_app import tools


class ViewInfo(object):

    def __init__(self, p_html_key, p_parent=None):

        self.parent = p_parent
        self._html_key = tools.get_safe_attribute_name(p_string=p_html_key)

    @property
    def html_key(self):

        if self.parent is None:
            return self._html_key

        else:
            return "%s_%s" % (self.parent.html_key, self._html_key)
