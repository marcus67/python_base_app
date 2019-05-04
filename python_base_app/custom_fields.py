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

import wtforms.widgets

from python_base_app import tools

class BaseCustomField(wtforms.Field):

    extra_css_classes = ""

    pass


class DurationField(BaseCustomField):
    widget = wtforms.widgets.TextInput()

    def __init__(self, *args, **largs):

        super().__init__(*args, **largs)

        self.invalid_data = None

    def _value(self):
        if self.invalid_data is not None:
            return self.invalid_data

        elif self.data is None:
            return '-'

        else:
            return tools.get_duration_as_string(p_seconds=self.data, p_include_seconds=False)

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = tools.get_string_as_duration(p_string=valuelist[0])
                self.invalid_data = None

            except Exception as e:

                self.invalid_data = valuelist[0]
                raise wtforms.validators.ValidationError(message=str(e))
        else:
            self.data = None
            self.invalid_data = None


class TimeField(BaseCustomField):
    widget = wtforms.widgets.TextInput()

    def __init__(self, *args, **largs):

        super().__init__(*args, **largs)
        self.invalid_data = None

    def _value(self):

        if self.invalid_data is not None:
            return self.invalid_data

        elif self.data is None:
            return '-'
        else:
            return tools.get_time_as_string(p_timestamp=self.data, p_include_seconds=False)

    def process_formdata(self, valuelist):
        if valuelist:

            try:
                self.data = tools.get_string_as_time(p_string=valuelist[0])

            except Exception as e:

                self.invalid_data = valuelist[0]
                raise wtforms.validators.ValidationError(message=str(e))

        else:
            self.data = None
            self.invalid_data = None

class BooleanField(BaseCustomField):

    widget = wtforms.widgets.CheckboxInput()

    extra_css_classes = "move-left"

    def __init__(self, *args, **largs):

        super().__init__(*args, **largs)

    def _value(self):


        return  self.data is not None and self.data

    def process_formdata(self, valuelist):
        if valuelist:

            try:
                self.data = 1 if valuelist[0] else 0

            except Exception as e:
                raise wtforms.validators.ValidationError(message=str(e))

        else:
            self.data = None
