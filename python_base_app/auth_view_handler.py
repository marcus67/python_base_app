# -*- coding: utf-8 -*-

# Copyright (C) 2019  Marcus Rickert
#
# See https://github.com/marcus67/python_base_app
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import flask
import flask.wrappers
import flask_login

import python_base_app
import some_flask_helpers

AUTH_BLUEPRINT_NAME = 'auth'
AUTH_BLUEPRINT_ADAPTER = some_flask_helpers.BlueprintAdapter()

LOGIN_ENDPOINT_NAME = "login"
LOGOUT_ENDPOINT_NAME = "logout"

_ = lambda x: x

# for pybabel:
_('Please log in to access this page.')


class User(flask_login.UserMixin):

    def __init__(self, p_username):
        self.username = p_username
        self.id = p_username

    def get_id(self):
        return self.id


class AuthViewHandler(object):

    def __init__(self, p_user_handler, p_app, p_url_prefix, p_login_view=None,
                 p_logged_out_endpoint=LOGIN_ENDPOINT_NAME):

        if p_login_view is None:
            p_login_view = self.login_view()

        self._user_handler = p_user_handler
        self._logged_out_endpoint = p_logged_out_endpoint
        self._login_view = p_login_view
        self._url_prefix = p_url_prefix

        self._login_manager = flask_login.LoginManager()
        self._login_manager.init_app(app=p_app)
        self._login_manager.login_view = AUTH_BLUEPRINT_NAME + '.' + LOGIN_ENDPOINT_NAME
        self._login_manager.user_loader(self.load_user)

        # See https://flask-login.readthedocs.io/en/latest/#how-it-works
        self._login_manager.session_protection = "strong"

        self._blueprint = flask.Blueprint(AUTH_BLUEPRINT_NAME, python_base_app.__name__)
        AUTH_BLUEPRINT_ADAPTER.assign_view_handler_instance(p_blueprint=self._blueprint, p_view_handler_instance=self)
        AUTH_BLUEPRINT_ADAPTER.check_view_methods()

        p_app.register_blueprint(self._blueprint, url_prefix=p_url_prefix)

    def load_user(self, p_user_id):

        if self._user_handler.is_admin(p_user_id):
            return User(p_username=p_user_id)

        else:
            return None

    def check_user(self, p_username, p_password):

        if self._user_handler.authenticate(p_username=p_username, p_password=p_password):
            return User(p_username=p_username)

        else:
            return None

    def login_view(self):

        return flask.wrappers.Response('''
        <CENTER>
            <FORM ACTION="" METHOD="post">
                <TABLE>
                    <TR>
                        <TD ALIGN="RIGHT">Username:</TD>
                        <TD><INPUT TYPE=text NAME=username></TD>
                    </TR>
                    <TR>
                        <TD ALIGN="RIGHT">Password:</TD>
                        <TD><input type=password name=password></TD>
                    </TR>
                    <TR>
                        <TD COLSPAN="2" ALIGN="CENTER"><INPUT TYPE=submit VALUE=Login></TD>
                    </TR>
                </TABLE>
            </FORM>
        </CENTER>
        ''')

    @AUTH_BLUEPRINT_ADAPTER.route_method(p_rule='/login', endpoint=LOGIN_ENDPOINT_NAME, methods=["GET", "POST"])
    def login(self):

        request = flask.globals.request

        if flask.globals.request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            user = self.check_user(p_username=username, p_password=password)

            if user is not None:
                flask_login.login_user(user)
                next_arg = request.args.get("next")

                if next_arg is None:
                    return flask.redirect("")

                else:
                    # if next_arg.startswith(self._url_prefix):
                    #     next_arg = next_arg[len(self._url_prefix):]
                    return flask.redirect(next_arg)

            else:
                next_arg = request.args.get("next")
                flask.flash(_('Wrong login or password'))

                if next_arg is None:
                    return flask.redirect(flask.url_for("auth.login"))

                else:
                    return flask.redirect(flask.url_for("auth.login", next=next_arg))

        else:
            return self._login_view()

    @AUTH_BLUEPRINT_ADAPTER.route_method(p_rule='/logout', endpoint=LOGOUT_ENDPOINT_NAME, methods=["POST"])
    def logout(self):

        flask_login.logout_user()
        return flask.redirect(flask.url_for(self._logged_out_endpoint))

    def destroy(self):
        AUTH_BLUEPRINT_ADAPTER.unassign_view_handler_instances()
