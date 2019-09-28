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

from setuptools import setup

setup_params = {
    # standard setup configuration
    "name" : "python-base-app",
    "version" : "0.1",
    "description" : "Generic tools for Python applications",
    "author" : "Marcus Rickert",
    "author_email" : "marcus.rickert@web.de",
    "url" : "https://github.com/marcus67/python_base_app",
    
    "install_requires" : [
        'alembic',
        'pytest',
        'requests', 
        'python-dateutil',
        'flask',
        'flask-wtf',
        'jinja2',
        'flask-blueprint'
    ],
    
    "packages" : [ 'python_base_app', 'python_base_app.test' ],
    "include_package_data": True,
    
    "long_description" : """Really long text here.""",

    # additional setup configuration used by CI stages
    "id" : "python-base-app",
    "revision" : "2",
}

if __name__ == '__main__':
    setup(**setup_params)
