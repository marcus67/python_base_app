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

DEBIAN_PACKAGE_BASE_NAME={{ var.setup.debian_package_name }}_{{ var.setup.version }}_{{ var.setup.debian_package_revision }}

if [ "${PUBLISH_USER}" == "" ] ; then
    echo "ERROR: The username for the publishing site must be provided in PUBLISH_USER"
    exit 1
fi

if [ "${PUBLISH_PASSWORD}" == "" ] ; then
    echo "ERROR: The password for the publishing site must be provided in PUBLISH_PASSWORD"
    exit 1
fi

if [ "${PUBLISH_URL}" == "" ] ; then
    echo "ERROR: The URL at the publishing site must be provided in PUBLISH_URL"
    exit 1
fi

SOURCE_FILE="{{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}.deb"
DEST_FILE="${PUBLISH_URL}/${DEBIAN_PACKAGE_BASE_NAME}.deb"

echo "Secure copy file '${SOURCE_FILE}' to '${DEST_FILE} '..."

if [ "${PUBLISH_PUBLIC_KEY}" != "" ] ; then
    set +e
    if grep --quiet "${PUBLISH_PUBLIC_KEY}" ~/.ssh/known_hosts ; then
        echo "Key '${PUBLISH_PUBLIC_KEY}' already found in list of known hosts..."
    else
        echo "Adding key '${PUBLISH_PUBLIC_KEY}' to list of known hosts..."
        echo "${PUBLISH_PUBLIC_KEY}" >> ~/.ssh/known_hosts
    fi
    set -e
else
    SCP_OPTIONS="-oStrictHostKeyChecking=no"
fi

export SSHPASS=${PUBLISH_PASSWORD}
sshpass -ve scp ${SCP_OPTIONS} ${SOURCE_FILE} ${PUBLISH_USER}@${DEST_FILE}
