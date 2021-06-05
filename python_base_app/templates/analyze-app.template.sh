#!/bin/bash

#    Copyright (C) 2019-2021  Marcus Rickert
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
# but only to python_base_app/templates/analyze-app.template.sh!                 #
##################################################################################

set -e
SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`

COVERAGE_FILE=${BASE_DIR}/coverage.xml
LOCAL_ENV_FILE=${BASE_DIR}/.dev-env-settings.sh

if [ -f ${LOCAL_ENV_FILE} ] ; then
  echo "Reading local environment settings from ${LOCAL_ENV_FILE}..."
  . ${LOCAL_ENV_FILE}
fi

set +e
export PATH=$PATH:/usr/bin/:/usr/local/bin:/vol/bin:/opt/bin
SONAR_SCANNER_BIN=$(which sonar-scanner)
set -e

if [ ! -x ${SONAR_SCANNER_BIN:-x} ] ; then
    echo "ERROR: No Sonar CLI found in path. Aborting..."
    exit 1
fi

echo "Using ${SONAR_SCANNER_BIN} for analysis..."

if [ ! -f ${COVERAGE_FILE} ] ; then
  echo "WARNING: file ${COVERAGE_FILE} was not found. No coverage results will be uploaded to SonarQube!"
fi

RETURN_CODE=0

if [ "${SONAR_HOST_URL}" == "" ] ; then
  echo "Environment variable 'SONAR_HOST_URL' not set!"
  RETURN_CODE=1
fi

if [ "${SONAR_LOGIN}" == "" ] ; then
  echo "Environment variable 'SONAR_LOGIN' not set!"
  RETURN_CODE=1
fi

if [ "${SONAR_PROJECT_KEY}" == "" ] ; then
  echo "Environment variable 'SONAR_PROJECT_KEY' not set!"
  RETURN_CODE=1
fi

if [ ${RETURN_CODE} -gt 0 ] ; then
  echo "ERROR: Environment settings incomplete! Aborting..."
  exit ${RETURN_CODE}
fi

cd ${BASE_DIR}

${SONAR_SCANNER_BIN} \
    -Dsonar.python.coverage.reportPaths=coverage.xml \
    -Dsonar.sources=. \
    -Dsonar.coverage.exclusions={%if var.setup.analyze_extra_coverage_exclusions %}{{ var.setup.analyze_extra_coverage_exclusions}},{%endif%}**__init__**,setup.py,contrib/** \
    -Dsonar.exclusions={%if var.setup.analyze_extra_exclusions %}{{ var.setup.analyze_extra_exclusions}},{%endif%}**/*.js,**/*.xml,**/*.css,{{ python_packages[0][2] }}/static/**,{{ python_packages[0][2] }}/templates/**,{{ python_packages[0][2] }}/alembic/**,contrib/** \
    -Dsonar.language=py \
    -Dsonar.host.url=${SONAR_HOST_URL} \
    -Dsonar.login=${SONAR_LOGIN} \
    -Dsonar.projectKey=${SONAR_PROJECT_KEY}
