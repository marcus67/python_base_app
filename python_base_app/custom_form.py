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

import flask_wtf


class ModelForm(flask_wtf.FlaskForm):

    def load_from_model(self, p_model):

        for field_name, field in self._fields.items():
            if field_name in p_model.__dict__:
                field.data = getattr(p_model, field_name, None)

    def differs_from_model(self, p_model):

        for field_name, field in self._fields.items():
            if field_name in p_model.__dict__:
                if field.data != getattr(p_model, field_name, None):
                    return True

        return False

    def save_to_model(self, p_model):

        for field_name, field in self._fields.items():
            if field_name in p_model.__dict__:
                setattr(p_model, field_name, field.data)
