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

{% if var.setup.build_debian_package -%}

# Make local scripts available to build process (e.g. dpkg-deb)
export PATH=${PATH}:${BASE_DIR}/docker/debian-package-build-tool

DEBIAN_PACKAGE_BASE_NAME={{ var.setup.debian_package_name }}_{{ var.setup.version }}_{{ var.setup.debian_package_revision }}

ROOT_DIR=${BASE_DIR}/{{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}

echo "Checking Debian build directory ${ROOT_DIR}..."
if [ -d ${ROOT_DIR}/DEBIAN ] ; then
  echo "Deleting Debian build directory ${ROOT_DIR}..."
  rm -rf ${ROOT_DIR}/
fi

TMP_DIR=${ROOT_DIR}/{{ var.setup.rel_tmp_dir }}
LIB_DIR=${ROOT_DIR}/{{ var.setup.rel_lib_dir }}
ETC_DIR=${ROOT_DIR}/{{ var.setup.rel_etc_dir }}
SYSTEMD_DIR=${ROOT_DIR}/{{ var.setup.rel_systemd_dir }}
TMPFILE_DIR=${ROOT_DIR}/{{ var.setup.rel_tmpfile_dir }}
SUDOERS_DIR=${ROOT_DIR}/{{ var.setup.rel_sudoers_dir }}
APPARMOR_DIR=${ROOT_DIR}/{{ var.setup.rel_apparmor_dir }}

mkdir -p ${TMP_DIR}
mkdir -p ${ETC_DIR}
mkdir -p ${LIB_DIR}

echo "Copying pip3.sh helper script..."
cp ${BASE_DIR}/bin/pip3.sh ${LIB_DIR}
{% endif %}

echo "Installing PIP packages required for building..."
{%- if var.setup.ci_stage_build_pip_dependencies|length > 0 %}
pip3 install {%- for package in var.setup.ci_stage_build_pip_dependencies %} {{package}}{% endfor %}
{%- endif %}


{% for package in python_packages %}
# Build PIP package {{ package[1] }}...
pushd . > /dev/null
cd {{ package[0] }}

{% if var.setup.build_debian_package -%}
{% for file_mapping in package[3].setup.debian_extra_files %}
TARGET_DIRECTORY=${ROOT_DIR}/$(dirname {{ file_mapping[1] }} )
mkdir -p ${TARGET_DIRECTORY}
echo "Deploying extra file '{{ file_mapping[0] }}' to '${ROOT_DIR}/{{ file_mapping[1] }}'..."
cp -f {{ file_mapping[0] }} ${ROOT_DIR}/{{ file_mapping[1] }}
{%- endfor %}
{% endif %}

{% if package[3].setup.git_metadata_file %}
echo "GIT_BRANCH=\"$(git rev-parse --abbrev-ref HEAD)\"" > {{ package[3].setup.git_metadata_file }}
echo "GIT_COMMIT_ID=\"$(git rev-parse HEAD)\"" >>  {{ package[3].setup.git_metadata_file }}
echo "GIT_AUTHOR_NAME=\"$(git log -1 --pretty=format:'%an')\"" >>  {{ package[3].setup.git_metadata_file }}
echo "GIT_AUTHOR_EMAIL=\"$(git log -1 --pretty=format:'%ae')\"" >>  {{ package[3].setup.git_metadata_file }}
{% endif %}

{% if package[3].setup.babel_rel_directory %}
pwd
pybabel compile -d {{ package[2] }}/{{ package[3].setup.babel_rel_directory }}
{% endif %}

python3 ./setup.py sdist

{% if var.setup.build_debian_package -%}
cp dist/{{ package[1] }} ${LIB_DIR}
{% endif %}
popd
{% endfor %}

{% if var.setup.build_debian_package -%}
cp -a ${BASE_DIR}/{{ var.setup.debian_build_dir}}/DEBIAN ${ROOT_DIR}

{% if var.setup.deploy_systemd_service %}
mkdir -p ${SYSTEMD_DIR}
cp ${BASE_DIR}/etc/{{ var.setup.name }}.service ${SYSTEMD_DIR}/{{ var.setup.name }}.service
{% endif %}

{% if var.setup.deploy_tmpfile_conf %}
mkdir -p ${TMPFILE_DIR}
cp ${BASE_DIR}/etc/{{ var.setup.name }}.tmpfile ${TMPFILE_DIR}/{{ var.setup.name }}.conf
{% endif %}

{% if var.setup.deploy_sudoers_file %}
mkdir -p ${SUDOERS_DIR}
cp ${BASE_DIR}/etc/{{ var.setup.name }}.sudo ${SUDOERS_DIR}/{{ var.setup.name }}
{% endif %}

{% if var.setup.deploy_apparmor_file %}
mkdir -p ${APPARMOR_DIR}
cp ${BASE_DIR}/etc/{{ var.setup.name }}.apparmor ${APPARMOR_DIR}/{{ var.setup.name }}.conf
{% endif %}

rm -f {{ var.setup.debian_build_dir}}/${DEBIAN_PACKAGE_BASE_NAME}.deb
cd ${BASE_DIR}
dpkg-deb --build {{ var.setup.debian_build_dir }}/${DEBIAN_PACKAGE_BASE_NAME}
{% endif %}
