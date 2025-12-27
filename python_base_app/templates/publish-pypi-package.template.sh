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
# but only to python_base_app/templates/publish-pypi-package.template.sh!        #
##################################################################################

set +e
SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`

if [ "${{ python_packages[0][5] }}" == "" ] ; then
    echo "ERROR: The API token for {{ python_packages[0][4] }} must be provided in {{ python_packages[0][5] }}"
    exit 1
else
    echo "INFO: The API token was provided in {{ python_packages[0][5] }}."
fi

if [ "${{ python_packages[0][6] }}" == "" ] ; then
    echo "INFO: The API user for {{ python_packages[0][4] }} was not provided in {{ python_packages[0][6] }}, will default to '__token__'"
    USER=__token__
else
    USER="${{ python_packages[0][6] }}"
fi

if [ "${{ python_packages[0][4] }}" == "" ] ; then
    echo "INFO: The API URL was not provided in {{ python_packages[0][4] }}, will default to '{{ python_packages[0][7] }}'"
    URL={{ python_packages[0][7] }}
else
    URL="${{ python_packages[0][4] }}"
fi

if [ "${{ python_packages[0][9] }}" == "" ] ; then
    echo "The setting {{ python_packages[0][9] }} was empty -> no deletion of PYPI package before upload."
else
    PACKAGE_LIST_URL="${{ python_packages[0][9] }}?per_page=100&order_by=created_at&sort=desc"
    echo "INFO: Package deletion requested. Package list URL = ${PACKAGE_LIST_URL}."

    PACKAGE_LIST=$(curl --header "PRIVATE-TOKEN: ${{ python_packages[0][5] }}" "${PACKAGE_LIST_URL}")
    RETURN_CODE=$?

    if [[ ${RETURN_CODE} -ne 0 ]] ; then
        echo "ERROR: packages cannot be listed. Return code: ${RETURN_CODE}!"
        exit 2
    fi

    ERROR_CODE=$(echo "${PACKAGE_LIST}" | jq '.error' 2> /dev/null)

    if [ ! "${ERROR_CODE}" == "" ] ; then
        echo "ERROR: PyPy server returns error ${ERROR_CODE}!"
        exit 3
    fi

    DELETE_URL=$(echo "${PACKAGE_LIST}" | jq '.[] | select (.name == "{{ python_packages[0][10] }}" and .version == "{{ python_packages[0][11] }}" )._links.delete_api_path')
    RETURN_CODE=$?

    if [[ ( ${RETURN_CODE} -ne 0 ) || ( "${DELETE_URL}" == "" ) ]] ; then
        echo "INFO: package '{{ python_packages[0][10] }}' in version '{{ python_packages[0][11] }}' does not seem to exist yet. Return code: ${RETURN_CODE}"
    else
        DELETE_URL=$(echo ${DELETE_URL}| tr -d '"')
        echo "INFO: Issuing deletion command using URL ${DELETE_URL}..."
        RESULT=$(curl --request DELETE --header "PRIVATE-TOKEN: ${{ python_packages[0][5] }}" ${DELETE_URL})
        RETURN_CODE=$?

        if [ ${RETURN_CODE} -gt 0 ] ; then
            echo "WARNING: result code of deletion command = ${RETURN_CODE}"
        fi
    fi
fi

echo "Installing PIP packages required for publishing..."
{%- if var.setup.ci_stage_publish_pip_package_pip_dependencies|length > 0 %}
pip3 install {%- for package in var.setup.ci_stage_publish_pip_package_pip_dependencies %} {{package}}{% endfor %}
{%- endif %}

echo "Publish PIP package {{ python_packages[0][1] }} to $URL with user $USER ..."

# See https://twine.readthedocs.io/en/latest/#using-twine
twine upload --repository-url $URL \
    --username $USER --password ${{ python_packages[0][5] }} dist/{{ python_packages[0][1] }}
