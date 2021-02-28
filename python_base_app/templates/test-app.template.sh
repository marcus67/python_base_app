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
# but only to python_base_app/templates/test-app.template.sh!                    #
##################################################################################

set -e
SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`
VIRTUAL_ENV_DIR=/{{ var.setup.rel_virtual_env_dir }}


set +e
#PYCOVERAGE_BIN=$(which coverage)
PYCOVERAGE_BIN=${VIRTUAL_ENV_DIR}/bin/coverage
set -e

if [ -x ${PYCOVERAGE_BIN} ] ; then
    echo "Using '${PYCOVERAGE_BIN}' for test coverage analysis..."
else
    echo "WARNING: No Python coverage tool found in path. No coverage stats will be collected..."
fi


{%- if arguments.use_dev_dir %}
export PATH={{ arguments.use_dev_dir }}:${PATH}
{%- else %}
if [ "${CI_DEBUG}" == "1" ] ; then
    echo "<<<<< Listing of {{ site_packages_dir }}....."
    ls -l {{ site_packages_dir }}
    echo ">>>>>"
fi
{%- endif %}
echo "Using PATH=${PATH}"

export PYTHONPATH={% for package in python_packages %}{{ package[0] }}:{% endfor %}${PYTHONPATH}
echo "Using PYTHONPATH=${PYTHONPATH}"

{%- if arguments.run_dir %}
cd {{ arguments.run_dir }}
{%- endif %}

if [ -f .coveragerc ] ; then
    if [ "${CI_DEBUG}" == "1" ] ; then
        echo "<<<<< Listing of execution directory..."
        ls -la
        echo ">>>>>"
        echo "<<<<< Contents of .coveragerc..."
        cat .coveragerc
        echo ">>>>>"
    fi
else
    echo "WARNING: could not find .coveragerc in project root! pycoverage will use defaults."
fi

set +e
RUN_TEST_BIN=`which {{ var.setup.run_test_suite }}`
set -e


if [ "${RUN_TEST_BIN}" == "" ] ; then
    echo "ERROR: Cannot find executable {{ var.setup.run_test_suite }} in PATH=${PATH}"
    exit 1
elif [ "${PYCOVERAGE_BIN}" == "" ] ; then
    echo "Running test script ${RUN_TEST_BIN}..."
    ${RUN_TEST_BIN}
else
    echo "Calling pycoverage 'erase'..."
    ${PYCOVERAGE_BIN} erase
    echo "Calling pycoverage 'run' for test script ${RUN_TEST_BIN}..."
    ${PYCOVERAGE_BIN} run ${RUN_TEST_BIN}
    echo "Calling pycoverage 'report'..."
    ${PYCOVERAGE_BIN} report
    ${PYCOVERAGE_BIN} html
fi
