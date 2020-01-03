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

TMP_DIR=/{{ var.setup.rel_tmp_dir }}
ETC_DIR=/{{ var.setup.rel_etc_dir }}
LOG_DIR=/{{ var.setup.rel_log_dir }}
SPOOL_DIR=/{{ var.setup.rel_spool_dir }}
SYSTEMD_DIR=/{{ var.setup.rel_systemd_dir }}
SUDOERS_DIR=/{{ var.setup.rel_sudoers_dir }}

if [ -x /usr/local/bin/pip3 ] ; then
    # If there is a pip in /usr/local it has probably been in installed/upgraded by pip itself. We had had better
    # take this one
    PIP3=/usr/local/bin/pip3
else
    # Otherwise take the one that has been installed by the Debian package...
    PIP3=/usr/bin/pip3
fi

{% if var.setup.create_group %}
if grep -q '{{ var.setup.group }}:' /etc/group ; then
    echo "Group '{{ var.setup.group }}' already exists."
else
    #echo "Adding group '{{ var.setup.group }}'..."
    if [ "${APP_GID}" == "" ] ; then
	addgroup {{ var.setup.group }}
    else
	addgroup --gid ${APP_GID} {{ var.setup.group }}
    fi
fi
{% endif %}

{% if var.setup.create_user %}
if grep -q '{{ var.setup.user }}:' /etc/passwd ; then
    echo "User '{{ var.setup.user }}' already exists."
else
    #echo "Adding user '{{ var.setup.user }}'..."
    if  [ "${APP_UID}" == "" ] ; then
	adduser --ingroup {{ var.setup.group }} --gecos "" --no-create-home --disabled-password {{ var.setup.user }}
    else
	adduser --ingroup {{ var.setup.group }} --uid ${APP_UID} --gecos "" --no-create-home --disabled-password {{ var.setup.user }}
    fi
fi
{% endif %}

set -e

{% for mapping in user_group_mappings %}
#echo "Adding user '{{ mapping[0] }}' to group '{{ mapping[1] }}'..."
adduser {{ mapping[0] }} {{ mapping[1] }}
{% endfor %}

echo "Creating directories..."
echo "    * ${LOG_DIR}"
mkdir -p ${LOG_DIR}
echo "    * ${SPOOL_DIR}"
mkdir -p ${SPOOL_DIR}

chown -R {{ var.setup.user }}.{{ var.setup.group }} ${ETC_DIR}
chown -R {{ var.setup.user }}.{{ var.setup.group }} ${LOG_DIR}
chown -R {{ var.setup.user }}.{{ var.setup.group }} ${SPOOL_DIR}

{% if var.setup.deploy_systemd_service %}
chown root.root ${SYSTEMD_DIR}/little-brother.service
{% endif %}
{% if var.setup.deploy_sudoers_file %}
chown root.root ${SUDOERS_DIR}/little-brother
{% endif %}

chmod -R og-rwx ${ETC_DIR}
chmod -R og-rwx ${LOG_DIR}
chmod -R og-rwx ${SPOOL_DIR}

${PIP3} --version
${PIP3} install wheel setuptools
echo "Installing PIP packages "
{% for package_name in python_packages %}
echo "  * {{ package_name[1] }}"
{% endfor %}
# see https://stackoverflow.com/questions/19548957/can-i-force-pip-to-reinstall-the-current-version
${PIP3} install --upgrade --force-reinstall {% for package_name in python_packages %}\
     ${TMP_DIR}/{{ package_name[1] }}{% endfor %}

{% for package_name in python_packages %}
echo "Removing installation file ${TMP_DIR}/{{ package_name[1] }}"...
rm ${TMP_DIR}/{{ package_name[1] }}
{% endfor %}
