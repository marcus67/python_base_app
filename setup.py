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

from os import path

from setuptools import setup

from python_base_app import settings

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(this_directory, 'requirements.txt')) as f:
    install_requires = f.read().splitlines()

setup_params = {
    # standard setup configuration

    "install_requires" : install_requires,

    "scripts": [
        "run_python_base_app_test_suite.py",
    ],

    "packages" : [ 'python_base_app', 'python_base_app.test' ],
    "include_package_data": True,
    
    "long_description" : long_description,
    "long_description_content_type" : 'text/markdown',
}

extended_setup_params = {
    # additional setup configuration used by CI stages

    "id": "python-base-app",
    "build_debian_package": False,
    "build_pypi_package": True,

    # for Testing extra CI PIP dependencies
    #"ci_pip_dependencies": { "some-package" },
    #"extra_pypi_indexes": { "master": ["TEST_PYPI_EXTRA_INDEX"] },

    "publish_pypi_package": { 'release': ( 'PYPI_API_URL', 'PYPI_API_TOKEN', 'TEST_PYPI_API_USER' ),
                              'master': ( 'TEST_PYPI_API_URL', 'TEST_PYPI_API_TOKEN', 'TEST_PYPI_API_USER' ) },
    "analyze": True
}
extended_setup_params.update(setup_params)

setup_params.update(settings.settings)
extended_setup_params.update(settings.extended_settings)
extended_setup_params.update(setup_params)


if __name__ == '__main__':
    setup(**setup_params)
