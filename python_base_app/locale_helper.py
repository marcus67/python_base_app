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

import gettext


class LocaleHelper(object):

    def __init__(self, p_locale_dir=None, p_locale_selector=None):

        self._locale_dir = p_locale_dir
        self._locale_selector = p_locale_selector
        self._langs = {}
        self._chained_helper = None

        if self._locale_selector is None:
            self._locale_selector = lambda: "en"

    def chain_helper(self, p_helper):

        self._chained_helper = p_helper

    def gettext(self, p_text):
        current_locale = self.locale

        if current_locale is None:
            current_locale = "en"

        gettext_func = self._langs.get(current_locale)

        if gettext_func is None:
            gettext_func = gettext.translation("messages", localedir=self._locale_dir,
                                               languages=[current_locale], fallback=True)
            self._langs[current_locale] = gettext_func

        if self._chained_helper is None:
            return gettext_func.gettext(p_text)

        else:
            return self._chained_helper.gettext(gettext_func.gettext(p_text))

    @property
    def locale_selector(self):
        return self._locale_selector

    @property
    def locale(self):
        return self.locale_selector()
