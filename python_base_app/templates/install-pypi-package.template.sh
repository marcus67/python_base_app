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
# but only to python_base_app/templates/install-debian-package.template.sh!      #
##################################################################################

set -e
SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`

cd ${BASE_DIR}

if [ -x /usr/local/bin/pip3 ] ; then
    # If there is a pip in /usr/local it has probably been in installed/upgraded by pip itself.
    # We had better take this one...
    PIP3=/usr/local/bin/pip3
else
    # Otherwise take the one that has been installed by the Debian package...
    PIP3=/usr/bin/pip3
fi

VIRTUAL_ENV_DIR="/var/lib/{{python_packages[0][3]['setup']['name']}}/virtualenv/bin"
PYTHON_BIN=$VIRTUAL_ENV_DIR/python3

if [ -d $VIRTUAL_ENV_DIR ] ; then
    echo "Virtual Python environment detected in $VIRTUAL_ENV_DIR..."
else
    echo "Creating makeshift Python interpreter script in $VIRTUAL_ENV_DIR..."
    mkdir -p $VIRTUAL_ENV_DIR
    echo "#!/bin/bash" > $PYTHON_BIN
    echo "python3 $@" >> $PYTHON_BIN
    chmod +x $PYTHON_BIN
fi

echo "Installing PIP package {{python_packages[0][1]}}..."
{%- if python_packages[0][3]['setup']['max_cpus'] %}
export MAX_CPUS={{ python_packages[0][3]["setup"]["max_cpus"]}}
# Prepend local bin dir so that our `make` is found for the Python wheel build process
export PATH=${BASE_DIR}/bin:${PATH}
{% endif %}

${PIP3} install --upgrade --force-reinstall dist/{{python_packages[0][1]}}
