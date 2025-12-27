#!/bin/bash

#    Copyright (C) 2019-2024  Marcus Rickert
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
# but only to python_base_app/templates/deploy-angular-app.template.sh!  #
##################################################################################

SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`
set -e

{% for package in python_packages %}
{%- if package[3].setup.angular_app_dir %}
pushd . > /dev/null
cd {{ package[0] }}
ANGULAR_BUILD_DIR=${BASE_DIR}/{{ package[3].setup.angular_deployment_source_directory }}
ANGULAR_DEPLOYMENT_DIR=${BASE_DIR}/{{ package [2] }}/{{ package[3].setup.angular_deployment_dest_directory }}
if [[ ! -d ${ANGULAR_DEPLOYMENT_DIR} ]] ; then
  echo "Create Angular deployment directory ${ANGULAR_DEPLOYMENT_DIR}..."
  mkdir -p ${ANGULAR_DEPLOYMENT_DIR}
fi
echo "Copying Angular build directory ${ANGULAR_BUILD_DIR} to ${ANGULAR_DEPLOYMENT_DIR}"
cp -uva ${ANGULAR_BUILD_DIR}/* ${ANGULAR_DEPLOYMENT_DIR}
popd > /dev/null
{%- endif %}
{% endfor %}
