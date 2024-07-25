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
# but only to python_base_app/templates/install-debian-package.template.sh!      #
##################################################################################

set -e
SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`
BIN_DIR=${BASE_DIR}/bin
PIP3=${BIN_DIR}/pip3.sh

cd ${BASE_DIR}

#VIRTUAL_ENV_DIR="/var/lib/{{python_packages[0][3]['setup']['name']}}/virtualenv/bin"
#PYTHON_BIN=$VIRTUAL_ENV_DIR/python3
#ORIG_PYTHON3_BIN=$(which python3)
#
#if [ "${ORIG_PYTHON3_BIN}" == "" ] ; then
#    echo "No Python3 interpreter found in PATH!"
#    exit 1
#fi
#
#if [ -d $VIRTUAL_ENV_DIR ] ; then
#    echo "Virtual Python environment detected in $VIRTUAL_ENV_DIR..."
#else
#    echo "Creating makeshift Python interpreter script in $VIRTUAL_ENV_DIR..."
#    mkdir -p $VIRTUAL_ENV_DIR
#    echo "#!/bin/bash" > $PYTHON_BIN
#    echo "${ORIG_PYTHON3_BIN} $@" >> $PYTHON_BIN
#    chmod +x $PYTHON_BIN
#fi

MAKE_BIN_DIR="{{ python_packages[0][3]['setup']['python_base_app_bin_dir'] }}"
{%- if python_packages[0][3]['setup']['max_cpus'] %}
export MAX_CPUS={{ python_packages[0][3]["setup"]["max_cpus"] }}
echo "Preparing customized make in ${MAKE_BIN_DIR} running ${MAX_CPUS} processes in parallel..."
# Prepend local bin dir so that our `make` is found for the Python wheel build process
export PATH=${MAKE_BIN_DIR}:${PATH}
# Export JOBS for the WAF framework
export JOBS=${MAX_CPUS}
hash -r
echo "Check: make found by 'which': $(which make)"
{% endif %}


echo "Installing PIP packages..."
{% for package in python_packages %}
echo "* {{package[0]}}/dist/{{package[1]}}"
{%- endfor %}
${PIP3} install --upgrade --force-reinstall {% for package in python_packages %} {{package[0]}}/dist/{{package[1]}} {% endfor %}
