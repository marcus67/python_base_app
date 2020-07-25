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

_ = lambda x: x


class BaseCustomField(wtforms.Field):
    extra_css_classes = ""


class DurationField(BaseCustomField):
    widget = wtforms.widgets.TextInput()

    def __init__(self, *args, **largs):

        super().__init__(*args, **largs)
        self.data = None
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
        self.data = None
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
        self.data = None

    def _value(self):

        return self.data is not None and self.data

    def process_formdata(self, valuelist):
        if valuelist:

            try:
                self.data = True if valuelist else False

            except Exception as e:
                raise wtforms.validators.ValidationError(message=str(e))

        else:
            self.data = None


def unlocalize(p_localized_values, p_value):
    for pair in p_localized_values:
        if pair[1] == p_value:
            return pair[0]

    return p_value


class LocalizedField(BaseCustomField):
    widget = wtforms.widgets.TextInput()

    def __init__(self, label='', validators=None, p_values=None, **kwargs):
        super().__init__(label, validators, **kwargs)

        self.localized_values = p_values

        if self.localized_values is None:
            self.localized_values = []

    def set_localized_values(self, p_values):

        self.localized_values = p_values

    def localize(self, p_value):

        for pair in self.localized_values:
            if pair[0] == p_value:
                return pair[1]

        return p_value

    def unlocalize(self, p_value):

        return unlocalize(p_localized_values=self.localized_values, p_value=p_value)

    def _value(self):

        return self.localize(p_value=self.data)

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = self.unlocalize(p_value=valuelist[0])

        else:
            self.data = None


class Uniqueness(object):

    def __init__(self, p_field_selectors=None):

        self._field_selectors = p_field_selectors
        self._forms = []

    def add_form(self, p_form):

        self._forms.append(p_form)
        p_form.uniqueness_instance = self

    def __call__(self, form, field):

        if self._field_selectors is None:
            form.uniqueness_instance(form, field)

        else:
            for selector in self._field_selectors:
                for other_form in self._forms:
                    if form is other_form:
                        continue

                    if selector(other_form).data == field.data:
                        msg = _("Value '{value}' already exists. Must be unique.")
                        raise wtforms.validators.ValidationError(msg.format(value=field.data))
