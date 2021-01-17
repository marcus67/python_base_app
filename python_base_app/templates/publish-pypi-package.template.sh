#!/bin/bash

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

##################################################################################
# Please, beware that this file has been generated! Do not make any changes here #
# but only to python_base_app/templates/publish-pypi-package.template.sh!        #
##################################################################################

set -e
SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`

if [ "${{ python_packages[0][5] }}" == "" ] ; then
    echo "ERROR: The API token for pypi.org must be provided in {{ python_packages[0][5] }}"
    exit 1
fi

echo "Publish PIP package {{ python_packages[0][1] }}..."

# See https://twine.readthedocs.io/en/latest/#using-twine
twine upload --repository-url {{ python_packages[0][4] }} \
    --username __token__ --password ${{ python_packages[0][5] }} dist/{{ python_packages[0][1] }}
