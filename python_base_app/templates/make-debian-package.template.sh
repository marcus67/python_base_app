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
# but only to python_base_app/templates/make-debian-package.template.sh!         #
##################################################################################

SCRIPT_DIR=`dirname $0`
BASE_DIR=`realpath ${SCRIPT_DIR}/..`
set -e

DEBIAN_PACKAGE_BASE_NAME={{ var.setup.debian_package_name }}_{{ var.setup.version }}_{{ var.setup.debian_package_revision }}

ROOT_DIR=${BASE_DIR}/{{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}

TMP_DIR=${ROOT_DIR}/{{ var.setup.rel_tmp_dir }}
ETC_DIR=${ROOT_DIR}/{{ var.setup.rel_etc_dir }}
SYSTEMD_DIR=${ROOT_DIR}/{{ var.setup.rel_systemd_dir }}
SUDOERS_DIR=${ROOT_DIR}/{{ var.setup.rel_sudoers_dir }}

mkdir -p ${TMP_DIR}
mkdir -p ${ETC_DIR}

{% for package in python_packages %}
# Build PIP package {{ package[1] }}...
pushd . > /dev/null
cd {{ package[0] }}

{% if package[3].setup.git_metadata_file %}
echo "GIT_BRANCH=\"$(git rev-parse --abbrev-ref HEAD)\"" > {{ package[3].setup.git_metadata_file }}
echo "GIT_COMMIT_ID=\"$(git rev-parse HEAD)\"" >>  {{ package[3].setup.git_metadata_file }}
echo "GIT_AUTHOR_NAME=\"$(git log -1 --pretty=format:'%an')\"" >>  {{ package[3].setup.git_metadata_file }}
echo "GIT_AUTHOR_EMAIL=\"$(git log -1 --pretty=format:'%ae')\"" >>  {{ package[3].setup.git_metadata_file }}
{% endif %}

python3 ./setup.py sdist
cp dist/{{ package[1] }} ${TMP_DIR}
popd
{% endfor %}

cp -ar ${BASE_DIR}/{{ var.setup.debian_build_dir}}/DEBIAN ${ROOT_DIR}

{% if var.setup.deploy_systemd_service %}
mkdir -p ${SYSTEMD_DIR}
cp ${BASE_DIR}/etc/{{ var.setup.name }}.service ${SYSTEMD_DIR}/{{ var.setup.name }}.service
{% endif %}

{% if var.setup.deploy_sudoers_file %}
mkdir -p ${SUDOERS_DIR}
cp ${BASE_DIR}/etc/{{ var.setup.name }}.sudo ${SUDOERS_DIR}/{{ var.setup.name }}
{% endif %}

rm -f {{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}.deb
cd ${BASE_DIR}
dpkg-deb --build {{ var.setup.debian_build_dir }}/${DEBIAN_PACKAGE_BASE_NAME}

