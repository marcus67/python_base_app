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

import flask

from flask_helpers import blueprint_adapter

import python_base_app

ACTUATOR_BLUEPRINT_NAME = "actuator"
ACTUATOR_BLUEPRINT_ADAPTER = blueprint_adapter.BlueprintAdapter()

class ActuatorViewHandler(object):

    def __init__(self, p_app, p_url_prefix):
        self._blueprint = flask.Blueprint(ACTUATOR_BLUEPRINT_NAME, python_base_app.__name__)
        ACTUATOR_BLUEPRINT_ADAPTER.assign_view_handler_instance(p_blueprint=self._blueprint,
            p_view_handler_instance=self)
        ACTUATOR_BLUEPRINT_ADAPTER.check_view_methods()
        p_app.register_blueprint(self._blueprint, url_prefix=p_url_prefix)

    @ACTUATOR_BLUEPRINT_ADAPTER.route_method(p_rule="/health")
    def health(self):

        return flask.Response("ok")

    def destroy(self):
        ACTUATOR_BLUEPRINT_ADAPTER.unassign_view_handler_instances()