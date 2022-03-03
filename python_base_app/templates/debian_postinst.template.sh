#! /bin/bash

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
# but only to python_base_app/templates/debian_postinst.template.sh!             #
##################################################################################


ETC_DIR=/{{ var.setup.rel_etc_dir }}
LOG_DIR=/{{ var.setup.rel_log_dir }}
SPOOL_DIR=/{{ var.setup.rel_spool_dir }}
LIB_DIR=/{{ var.setup.rel_lib_dir }}
VIRTUAL_ENV_DIR=/{{ var.setup.rel_virtual_env_dir }}
SYSTEMD_DIR=/{{ var.setup.rel_systemd_dir }}
TMPFILE_DIR=/{{ var.setup.rel_tmpfile_dir }}
SUDOERS_DIR=/{{ var.setup.rel_sudoers_dir }}
APPARMOR_DIR=/{{ var.setup.rel_apparmor_dir }}

ROOT_DIR=
SCRIPT_DIR=$(dirname ${BASH_SOURCE[0]})
INSTALL_BASE_DIR=$(realpath $SCRIPT_DIR/..)
BIN_DIR=${INSTALL_BASE_DIR}/bin

{% if generic_script %}

echo "Creating lib directories..."
echo "    * ${LIB_DIR}"
mkdir -p ${LIB_DIR}

echo "Running generic installation script with base directory located in $INSTALL_BASE_DIR..."

if [ ! "$EUID" == "0" ] ; then
    echo "ERROR: You have to be root to call this script."
    exit 2
fi

PIP3=${SCRIPT_DIR}/pip3.sh
chmod +x ${PIP3}
echo "Downloading Pip packages to $LIB_DIR..."
{%- for package_name in python_packages %}
${PIP3} download -d $LIB_DIR --no-deps {{ package_name[2] }}=={{ package_name[11] }}
{% endfor %}

echo "Checking if all Pip packages have been downloaded to $LIB_DIR..."
{%- for package_name in python_packages %}
if [ ! -f $LIB_DIR/{{ package_name[1] }} ] ; then
  echo "ERROR: package {{ package_name[1] }} not found in $LIB_DIR!"
  echo "Download from test.pypi.org and execute again."
  exit 2
else
  echo "Package {{ package_name[1] }} was found."
fi
{% endfor %}

{%- if var.setup.deploy_systemd_service %}
mkdir -p ${SYSTEMD_DIR}
cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.name }}.service ${SYSTEMD_DIR}/{{ var.setup.name }}.service
echo "Execute systemctl daemon-reload..."
systemctl daemon-reload
{%- endif %}

{%- if var.setup.deploy_tmpfile_conf %}
mkdir -p ${TMPFILE_DIR}
cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.name }}.tmpfile ${TMPFILE_DIR}/{{ var.setup.name }}.conf
{%- endif %}

{%- if var.setup.deploy_sudoers_file %}
mkdir -p ${SUDOERS_DIR}
cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.name }}.sudo ${SUDOERS_DIR}/{{ var.setup.name }}
{%- endif %}

{%- if var.setup.deploy_apparmor_file %}
mkdir -p ${APPARMOR_DIR}
cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.name }}.apparmor ${APPARMOR_DIR}/{{ var.setup.name }}.conf
{%- endif %}

{%- for package in python_packages %}
{%- if var.setup.build_debian_package -%}
{%- for file_mapping in package[3].setup.debian_extra_files %}
TARGET_DIRECTORY=${ROOT_DIR}/$(dirname {{ file_mapping[1] }} )
mkdir -p ${TARGET_DIRECTORY}
echo "Deploying extra file '$INSTALL_BASE_DIR/{{ file_mapping[0] }}' to '${ROOT_DIR}/{{ file_mapping[1] }}'..."
cp -f $INSTALL_BASE_DIR/{{ file_mapping[0] }} ${ROOT_DIR}/{{ file_mapping[1] }}
{%- endfor %}
{%- endif %}
{% endfor %}

{% else %}

PIP3=${LIB_DIR}/pip3.sh
chmod +x ${PIP3}
# endif for if generic_script
{%- endif %}

{%- if var.setup.create_group %}
if grep -q '{{ var.setup.group }}:' /etc/group ; then
    echo "Group '{{ var.setup.group }}' already exists. Skipping group creation."
else
    #echo "Adding group '{{ var.setup.group }}'..."
    if [ "${APP_GID}" == "" ] ; then
        groupadd {{ var.setup.group }}
    else
	      groupadd --gid ${APP_GID} {{ var.setup.group }}
    fi
fi
{%- endif %}

{%- if var.setup.create_user %}
if grep -q '{{ var.setup.user }}:' /etc/passwd ; then
    echo "User '{{ var.setup.user }}' already exists. Skipping user creation."
else
    if  [ "${APP_UID}" == "" ] ; then
#        adduser --gid {{ var.setup.group }} --gecos "" --no-create-home --disabled-password {{ var.setup.user }}
        useradd --gid {{ var.setup.group }} --no-create-home {{ var.setup.user }}
    else
#        adduser --gid {{ var.setup.group }} --uid ${APP_UID} --gecos "" --no-create-home --disabled-password {{ var.setup.user }}
        useradd --gid {{ var.setup.group }} --uid ${APP_UID} --no-create-home {{ var.setup.user }}
    fi
fi
{%- endif %}

set -e

{%- for mapping in user_group_mappings %}
usermod -aG {{ mapping[1] }} {{ mapping[0] }}
{% endfor %}

echo "Creating directories..."
echo "    * ${LOG_DIR}"
mkdir -p ${LOG_DIR}
echo "    * ${SPOOL_DIR}"
mkdir -p ${SPOOL_DIR}
echo "    * ${LIB_DIR}"
mkdir -p ${LIB_DIR}

{% for file_mapping in var.setup.debian_templates %}
if [ -f {{ file_mapping[1] }} ] ; then
  echo "Template '{{ file_mapping[0] }}' already exists as '{{ file_mapping[1] }}' -> SKIPPING"
else
  echo "Deploying template file '{{ file_mapping[0] }}' to '{{ file_mapping[1] }}'..."
  cp -f {{ file_mapping[0] }} {{ file_mapping[1] }}
fi
{%- endfor %}

{% for script in var.setup.scripts %}
echo "Creating symbolic link /usr/local/bin/{{ script }} --> ${VIRTUAL_ENV_DIR}/bin/{{ script }}..."
ln -fs ${VIRTUAL_ENV_DIR}/bin/{{ script }} /usr/local/bin/{{ script }}
{%- endfor %}

echo "Creating virtual Python environment in ${VIRTUAL_ENV_DIR}..."

virtualenv -p /usr/bin/python3 ${VIRTUAL_ENV_DIR}

echo "Setting ownership..."
echo "    * {{ var.setup.user }}.{{ var.setup.group }} ${ETC_DIR}"
chown -R {{ var.setup.user }}.{{ var.setup.group }} ${ETC_DIR}
echo "    * {{ var.setup.user }}.{{ var.setup.group }} ${LOG_DIR}"
chown -R {{ var.setup.user }}.{{ var.setup.group }} ${LOG_DIR}
echo "    * {{ var.setup.user }}.{{ var.setup.group }} ${SPOOL_DIR}"
chown -R {{ var.setup.user }}.{{ var.setup.group }} ${SPOOL_DIR}
echo "    * {{ var.setup.user }}.{{ var.setup.group }} ${LIB_DIR}"
chown -R {{ var.setup.user }}.{{ var.setup.group }} ${LIB_DIR}

{% for file_mapping in var.setup.debian_templates %}
echo "    * {{ var.setup.user }}.{{ var.setup.group }} {{ file_mapping[1] }}"
chown {{ var.setup.user }}.{{ var.setup.group }} {{ file_mapping[1] }}
{%- endfor %}

{%- if var.setup.deploy_systemd_service %}
echo "    * ${SYSTEMD_DIR}/{{ var.setup.name }}.service"
chown root.root ${SYSTEMD_DIR}/{{ var.setup.name }}.service
{% endif %}
{%- if var.setup.deploy_tmpfile_service %}
echo "    * ${TMPFILE_DIR}/{{ var.setup.name }}.conf"
chown root.root ${TMPFILE_DIR}/{{ var.setup.name }}.conf
{% endif %}
{%- if var.setup.deploy_sudoers_file %}
echo "    * ${SUDOERS_DIR}"
chown root.root ${SUDOERS_DIR}
echo "    * ${SUDOERS_DIR}/{{ var.setup.name }}"
chown root.root ${SUDOERS_DIR}/{{ var.setup.name }}
{% endif %}
{%- if var.setup.deploy_apparmor_file %}
echo "    * ${APPARMOR_DIR}/{{ var.setup.name }}.conf"
chown root.root ${APPARMOR_DIR}/{{ var.setup.name }}.conf
{% endif %}

echo "Setting permissions..."
echo "    * ${ETC_DIR}"
chmod -R og-rwx ${ETC_DIR}
echo "    * ${LOG_DIR}"
chmod -R og-rwx ${LOG_DIR}
echo "    * ${SPOOL_DIR}"
chmod -R og-rwx ${SPOOL_DIR}

{% for file_mapping in var.setup.debian_templates %}
echo "    * {{ var.setup.user }}.{{ var.setup.group }} {{ file_mapping[1] }}"
chmod og-rwx {{ file_mapping[1] }}
{%- endfor %}

${PIP3} --version
${PIP3} install wheel # setuptools
echo "Installing PIP packages..."
{%- for package_name in python_packages %}
echo "  * {{ package_name[1] }}"
{%- endfor %}
# see https://stackoverflow.com/questions/19548957/can-i-force-pip-to-reinstall-the-current-version
${PIP3} install --upgrade --force-reinstall {% for package_name in python_packages %}\
     ${LIB_DIR}/{{ package_name[1] }}{% endfor %}

{% for package_name in python_packages %}
echo "Removing installation file ${LIB_DIR}/{{ package_name[1] }}..."
rm ${LIB_DIR}/{{ package_name[1] }}
{%- endfor %}
