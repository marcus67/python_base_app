#! /bin/bash

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
# but only to python_base_app/templates/debian_postinst.template.sh!             #
##################################################################################

##################################################################################
# PARAMETERS                                                                     #
##################################################################################
# When set, will deactivate portions that are not applicable to Docker containers
RUNNING_IN_DOCKER=${RUNNING_IN_DOCKER:-}

# When set, contains an extra PIP index to download from
# This will be required when trying to install the version of the `master` branch since the required PIP packages
# may not be available ot pypi.org yet. In this case, add the extra index https://test.pypi.org/simple/
TEST_PYPI_EXTRA_INDEX=${TEST_PYPI_EXTRA_INDEX:-}

# When set, will create the application user with a specific user id
APP_UID=${APP_UID:-}

# When set, will create the application group with a specific group id
APP_GID=${APP_UID:-}

##################################################################################

if [ -f /etc/os-release ] ; then
  . /etc/os-release
else
  echo "Cannot read /etc/os-release!"
  exit 2
fi

echo "Detected operating system architecture '${ID}'."

function add_group() {
  group_name=$1
  group_id=$2

  if [ "$ID" == "alpine" ] ; then
    if [ "${group_id}" == "" ] ; then
      addgroup ${group_name}
    else
      addgroup -g ${group_id} ${group_name}
    fi
  else
    if [ "${group_id}" == "" ] ; then
      groupadd {{ var.setup.group }}
    else
      groupadd --gid ${group_id} ${group_name}
    fi

  fi
}

function add_user() {
  user_name=$1
  group_name=$2
  user_id=$3

  if [ "$ID" == "alpine" ] ; then
    if  [ "${user_id}" == "" ] ; then
        adduser -G ${group_name} -g "" -H -D ${user_name}
    else
        adduser -G ${group_name} -u ${user_id} -g "" -H -D ${user_name}
    fi
  else
    if  [ "${user_id}" == "" ] ; then
        useradd --gid ${group_name} --no-create-home ${user_name}
    else
        useradd --gid ${group_name} --uid ${user_id} --no-create-home ${user_name}
    fi
  fi

}

function add_user_to_group() {
  user_name=$1
  group_name=$2

  if [ "$ID" == "alpine" ] ; then
    adduser ${user_name} ${group_name}
  else
    usermod -aG ${group_name} ${user_name}
  fi
}

export VIRTUAL_ENV_DIR=/{{ var.setup.rel_virtual_env_dir }}

ETC_DIR=/{{ var.setup.rel_etc_dir }}
LOG_DIR=/{{ var.setup.rel_log_dir }}
SPOOL_DIR=/{{ var.setup.rel_spool_dir }}
LIB_DIR=/{{ var.setup.rel_lib_dir }}
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
if [ "$RUNNING_IN_DOCKER" == "" ] ; then
  mkdir -p ${SYSTEMD_DIR}
  cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.id }}.service ${SYSTEMD_DIR}/{{ var.setup.id }}.service
fi
{%- endif %}

{%- if var.setup.deploy_tmpfile_conf %}
mkdir -p ${TMPFILE_DIR}
cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.id }}.tmpfile ${TMPFILE_DIR}/{{ var.setup.id }}.conf
{%- endif %}

{%- if var.setup.deploy_sudoers_file %}
mkdir -p ${SUDOERS_DIR}
cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.id }}.sudo ${SUDOERS_DIR}/{{ var.setup.id }}
{%- endif %}

{%- if var.setup.deploy_apparmor_file %}
mkdir -p ${APPARMOR_DIR}
cp ${INSTALL_BASE_DIR}/etc/{{ var.setup.id }}.apparmor ${APPARMOR_DIR}/{{ var.setup.id }}.conf
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
    add_group {{ var.setup.group }} ${APP_GID}
fi
{%- endif %}

{%- if var.setup.create_user %}
if grep -q '{{ var.setup.user }}:' /etc/passwd ; then
    echo "User '{{ var.setup.user }}' already exists. Skipping user creation."
else
    add_user {{ var.setup.user }} {{ var.setup.group }} ${APP_UID}
fi
{%- endif %}

set -e

{%- for mapping in user_group_mappings %}
  add_user_to_group {{ mapping[0] }} {{ mapping[1] }}
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

if [ "${VIRTUAL_ENV_DIR}" != "" ] ; then
{% for script in var.setup.scripts %}
echo "Creating symbolic link /usr/local/bin/{{ script }} --> ${VIRTUAL_ENV_DIR}/bin/{{ script }}..."
ln -fs ${VIRTUAL_ENV_DIR}/bin/{{ script }} /usr/local/bin/{{ script }}
{%- endfor %}

echo "Creating virtual Python environment in ${VIRTUAL_ENV_DIR}..."

virtualenv -p /usr/bin/python3 ${VIRTUAL_ENV_DIR}
echo "Activating virtual Python environment in ${VIRTUAL_ENV_DIR}..."
. ${VIRTUAL_ENV_DIR}/bin/activate
fi

echo "Setting ownership..."
echo "    * {{ var.setup.user }}:{{ var.setup.group }} ${ETC_DIR}"
chown -R {{ var.setup.user }}:{{ var.setup.group }} ${ETC_DIR}
echo "    * {{ var.setup.user }}:{{ var.setup.group }} ${LOG_DIR}"
chown -R {{ var.setup.user }}:{{ var.setup.group }} ${LOG_DIR}
echo "    * {{ var.setup.user }}:{{ var.setup.group }} ${SPOOL_DIR}"
chown -R {{ var.setup.user }}:{{ var.setup.group }} ${SPOOL_DIR}
echo "    * {{ var.setup.user }}:{{ var.setup.group }} ${LIB_DIR}"
chown -R {{ var.setup.user }}:{{ var.setup.group }} ${LIB_DIR}

{% for file_mapping in var.setup.debian_templates %}
echo "    * {{ var.setup.user }}:{{ var.setup.group }} {{ file_mapping[1] }}"
chown {{ var.setup.user }}:{{ var.setup.group }} {{ file_mapping[1] }}
{%- endfor %}

{%- if var.setup.deploy_systemd_service %}
  if [ "$RUNNING_IN_DOCKER" == "" ] ; then
  echo "    * ${SYSTEMD_DIR}/{{ var.setup.id }}.service"
  chown root.root ${SYSTEMD_DIR}/{{ var.setup.id }}.service
  fi
{%- endif %}

{%- if var.setup.deploy_tmpfile_service %}
echo "    * ${TMPFILE_DIR}/{{ var.setup.id }}.conf"
chown root.root ${TMPFILE_DIR}/{{ var.setup.id }}.conf
{% endif %}
{%- if var.setup.deploy_sudoers_file %}
echo "    * ${SUDOERS_DIR}"
chown root.root ${SUDOERS_DIR}
echo "    * ${SUDOERS_DIR}/{{ var.setup.id }}"
chown root.root ${SUDOERS_DIR}/{{ var.setup.id }}
{% endif %}
{%- if var.setup.deploy_apparmor_file %}
echo "    * ${APPARMOR_DIR}/{{ var.setup.id }}.conf"
chown root.root ${APPARMOR_DIR}/{{ var.setup.id }}.conf
{% endif %}

echo "Setting permissions..."
echo "    * ${ETC_DIR}"
chmod -R og-rwx ${ETC_DIR}
echo "    * ${LOG_DIR}"
chmod -R og-rwx ${LOG_DIR}
echo "    * ${SPOOL_DIR}"
chmod -R og-rwx ${SPOOL_DIR}

{% for file_mapping in var.setup.debian_templates %}
echo "    * {{ var.setup.user }}:{{ var.setup.group }} {{ file_mapping[1] }}"
chmod og-rwx {{ file_mapping[1] }}
{%- endfor %}

echo "Upgrading packages 'wheel' and 'setuptools'..."
${PIP3} install wheel setuptools
echo "Installing PIP packages..."
{%- for package_name in python_packages %}
echo "  * {{ package_name[1] }}"
{%- endfor %}
# see https://stackoverflow.com/questions/19548957/can-i-force-pip-to-reinstall-the-current-version
${PIP3} install --upgrade --ignore-installed {% for package_name in python_packages %}\
     ${LIB_DIR}/{{ package_name[1] }}{% endfor %}

if [ "${VIRTUAL_ENV_DIR}" != "" ] ; then
  echo "Changing ownership of virtual environment ${VIRTUAL_ENV_DIR} to {{ var.setup.user }}:{{ var.setup.group }}..."
  chown -R {{ var.setup.user }}:{{ var.setup.group }} ${VIRTUAL_ENV_DIR}
fi


{% for package_name in python_packages %}
echo "Removing installation file ${LIB_DIR}/{{ package_name[1] }}..."
rm ${LIB_DIR}/{{ package_name[1] }}
{%- endfor %}

{%- if var.setup.deploy_systemd_service %}
if [ "$RUNNING_IN_DOCKER" == "" ] ; then
  echo "Execute systemctl daemon-reload..."
  set +e
  systemctl daemon-reload
  set -e
fi
{%- endif %}
