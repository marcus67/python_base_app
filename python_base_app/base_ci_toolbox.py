# -*- coding: utf-8 -*-

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

import argparse
import collections
import copy
import logging
import os
import os.path
import stat
import subprocess
import sys
import time

import jinja2

import python_base_app
from python_base_app import exceptions
from python_base_app import log_handling
from python_base_app import tools

MODULE_NAME = "base_ci_toolbox"

STAGE_BUILD_PACKAGE = "BUILD"
STAGE_BUILD_DOCKER_IMAGES = "BUILD_DOCKER_IMAGES"
STAGE_INSTALL = "INSTALL"
STAGE_INSTALL_PYPI_PACKAGE = "INSTALL-PYPI-PACKAGE"
STAGE_PUBLISH_PACKAGE = "PUBLISH-PACKAGE"
STAGE_PUBLISH_PYPI_PACKAGE = "PUBLISH-PYPI-PACKAGE"
STAGE_TEST = "TEST"
STAGE_ANALYZE = "ANALYZE"
STAGE_TEARDOWN = "TEARDOWN"
STAGE_PREPARE = "PREPARE"

GITLAB_CI_FILE = '.gitlab-ci.yml'
GITLAB_CI_TEMPLATE = 'gitlab-ci.template.yml'

GIT_PY_FILE_PATH = '{module_name}/git.py'
GIT_PY_TEMPLATE = 'git.template.py'

CIRCLE_CI_FILE = '.circleci/config.yml'
CIRCLE_CI_TEMPLATE = 'circle-ci.template.yml'

PYCOVERAGE_FILE_PATH = '.coveragerc'
PYCOVERAGE_TEMPLATE = 'coveragerc.template'

CODACY_FILE_PATH = '.codacy.yml'
CODACY_TEMPLATE = 'codacy.template.yml'

DEBIAN_CONTROL_FILE_PATH = '{debian_build_dir}/DEBIAN/control'
DEBIAN_CONTROL_TEMPLATE = 'debian_control.template.conf'

DEBIAN_POSTINST_FILE_PATH = '{debian_build_dir}/DEBIAN/postinst'
DEBIAN_POSTINST_TEMPLATE = 'debian_postinst.template.sh'

GENERIC_INSTALLATION_SCRIPT_FILE_PATH = '{bin_dir}/generic-install.sh'
GENERIC_INSTALLATION_SCRIPT_TEMPLATE = 'debian_postinst.template.sh'

MAKE_DEBIAN_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/make-debian-package.sh'
MAKE_DEBIAN_PACKAGE_SCRIPT_TEMPLATE = 'make-debian-package.template.sh'

BUILD_DOCKER_IMAGE_SCRIPT_FILE_PATH = '{bin_dir}/build-docker-images.sh'
BUILD_DOCKER_IMAGE_SCRIPT_TEMPLATE = 'build-docker-images.template.sh'

INSTALL_DEBIAN_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/install-debian-package.sh'
INSTALL_DEBIAN_PACKAGE_SCRIPT_TEMPLATE = 'install-debian-package.template.sh'

INSTALL_PYPI_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/install-pypi-package.sh'
INSTALL_PYPI_PACKAGE_SCRIPT_TEMPLATE = 'install-pypi-package.template.sh'

PUBLISH_DEBIAN_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/publish-debian-package.sh'
PUBLISH_DEBIAN_PACKAGE_SCRIPT_TEMPLATE = 'publish-debian-package.template.sh'

PUBLISH_PYPI_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/publish-pypi-package.sh'
PUBLISH_PYPI_PACKAGE_SCRIPT_TEMPLATE = 'publish-pypi-package.template.sh'

TEST_APP_SCRIPT_FILE_PATH = '{bin_dir}/test-app.sh'
TEST_APP_SCRIPT_TEMPLATE = 'test-app.template.sh'

ANALYZE_APP_SCRIPT_FILE_PATH = '{bin_dir}/analyze-app.sh'
ANALYZE_APP_SCRIPT_TEMPLATE = 'analyze-app.template.sh'

BEACON_INTERVAL = 60  # seconds

VarStatus = collections.namedtuple("VarInfo", "source_name description target_name")

PREDEFINED_ENV_VARIABLES = [
    VarStatus('FORCED_GIT_BRANCH', "Forced Git branch name (possibly overriding CI/CD branch names)", "GIT_BRANCH"),
    VarStatus('CIRCLE_BRANCH', "Circle CI Git branch name", "GIT_BRANCH"),
    VarStatus('CI_COMMIT_BRANCH', "GitLab CI/CD Git branch name", "GIT_BRANCH"),
    VarStatus('DOCKER_REGISTRY_HOST_NAME', "Docker registry host name", "docker_registry"),
    VarStatus('DOCKER_REGISTRY_ORG_UNIT', "Docker registry organisational unit", "docker_registry_org_unit"),
    VarStatus('DOCKER_REGISTRY_USER', "Docker registry login user", "docker_registry_user"),
    VarStatus('MAX_CPUS', "Maximum number of parallel CPUs/threads to be used during build", "max_cpus"),
]

DEFAULT_PYPI_REPOSITORY = "https://pypi.org"
DEFAULT_PYPI_TOKEN_ENV_NAME = "PYPI_API_TOKEN"

predefined_env_variables = None

default_setup = {
    "docker_image_make_package": "accso/docker-python-app:latest",
    "docker_image_test": "accso/docker-python-app:latest",
    "docker_image_docker": "marcusrickert/docker-docker-ci:release-0.9.1",
    "docker_image_analyze": "accso/docker-python-app:latest",
    "ci_toolbox_script": "ci_toolbox.py",
    "ci_stage_build_package": STAGE_BUILD_PACKAGE,
    "ci_stage_build_docker_images": STAGE_BUILD_DOCKER_IMAGES,
    "ci_stage_install": STAGE_INSTALL,
    "ci_stage_install_pypi_package": STAGE_INSTALL_PYPI_PACKAGE,
    "ci_stage_test": STAGE_TEST,
    "ci_stage_analyze": STAGE_ANALYZE,
    "ci_stage_teardown": STAGE_TEARDOWN,
    "ci_stage_publish_package": STAGE_PUBLISH_PACKAGE,
    "ci_stage_publish_pypi_package": STAGE_PUBLISH_PYPI_PACKAGE,
    "require_teardown": False,
    "bin_dir": "bin",
    "test_dir": "test",
    "run_test_suite": "run_{module_name}_test_suite.py",
    "run_test_suite_no_venv": "run_{module_name}_test_suite_no_venv.py",
    "contrib_dir": "contrib",
    "rel_tmp_dir": "tmp",
    "rel_etc_dir": "etc/{name}",
    "rel_log_dir": "var/log/{name}",
    "rel_spool_dir": "var/spool/{name}",
    "rel_lib_dir": "var/lib/{name}",
    "rel_virtual_env_dir": "var/lib/{name}/virtualenv",
    "rel_systemd_dir": "lib/systemd/system",
    "rel_tmpfile_dir": "usr/lib/tmpfiles.d",
    "rel_sudoers_dir": "etc/sudoers.d",
    "rel_apparmor_dir": "etc/apparmor.d",
    "git_metadata_file": "{module_name}/git_metadata.py",
    "user": "{name}",
    "group": "{name}",
    "user_group_mappings": [],
    "create_usr": False,
    "create_group": False,
    "deploy_systemd_service": False,
    "deploy_tmpfile_conf": False,
    "deploy_sudoers_file": False,
    "deploy_apparmor_file": False,
    "version": "0.1",
    "target_alembic_version": None,
    "build_debian_package": True,
    "debian_build_dir": "debian",
    "debian_package_name": "{name}",
    "debian_package_revision": "1",
    "debian_package_section": "base",
    "debian_package_priority": "optional",
    "debian_package_architecture": "amd64",
    "debian_dependencies": [],
    "debian_extra_files": [],
    "debian_templates": [],
    "install_requires": [],
    "contributing_setups": [],
    "publish_debian_package": [],
    "build_pypi_package": False,
    "publish_pypi_package": [],
    "publish_docker_images": [],
    "publish_latest_docker_image": "",
    "docker_registry": "docker.io",
    "docker_registry_user": "[DOCKER_REGISTRY_USER_NOT_SET]",
    "docker_registry_org_unit": "[DOCKER_REGISTRY_ORG_UNIT_NOT_SET]",
    "docker_context_dir": "docker",
    "docker_contexts": [],
    "babel_rel_directory": None,
    "generate_generic_install": False,
    "max_cpus": None,
    "analyze": False,
    "analyze_extra_coverage_exclusions": None,
    "analyze_extra_exclusions": None,
    "script_timeout": 600,
}

logger:logging.Logger = None


def get_module_dir(p_module):
    return os.path.dirname(p_module.__file__)


def get_python_package_name(p_var):
    return "{name}-{version}.tar.gz".format(**(p_var["setup"]))


def get_predefined_environment_variables():
    global logger
    global predefined_env_variables

    if predefined_env_variables is None:
        predefined_env_variables = {}

        for var_info in PREDEFINED_ENV_VARIABLES:
            value = os.getenv(var_info.source_name)

            if value is not None:
                if var_info.target_name in predefined_env_variables:
                    msg = "New value '{value}' found in environment with value ({name}) to be used for '{target_name}' WILL BE IGNORED!"
                    logger.warning(msg.format(name=var_info.source_name, value=value, target_name=var_info.target_name))

                else:
                    msg = "{description} ({name}) found in environment with value '{value}' to be used for '{target_name}'"
                    logger.info(msg.format(name=var_info.source_name, description=var_info.description, value=value,
                                           target_name=var_info.target_name))
                    predefined_env_variables[var_info.target_name] = value

    return predefined_env_variables


def expand_vars(p_vars):
    while True:
        change_done = False

        for (key, value) in p_vars.items():
            if isinstance(value, str):
                new_value = value.format(**p_vars)

                if new_value != value:
                    change_done = True
                    p_vars[key] = new_value

        if not change_done:
            break


def get_vars(p_setup_params):
    setup = copy.copy(default_setup)
    setup.update(p_setup_params)

    setup["module_name"] = setup["name"].replace("-", "_")
    setup.update(get_predefined_environment_variables())

    expand_vars(setup)

    # store bin path so that tools can be found
    setup["python_base_app_bin_dir"] = os.path.realpath(os.path.join(os.path.dirname(__file__), "../bin"))

    return {"setup": setup}


def load_setup_module(p_dir, p_module_name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(p_module_name, "{dir}/setup.py".format(dir=p_dir))
    setup_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup_module)
    return setup_module


def load_contributing_setup_modules(p_main_setup_module):
    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    contrib_setup_modules = []

    for contrib_module_name in var["setup"]["contributing_setups"]:
        module = load_setup_module(p_dir=os.path.join(var["setup"]["contrib_dir"], contrib_module_name),
                                   p_module_name=contrib_module_name)
        contrib_setup_modules.append(module)

    return contrib_setup_modules


def get_site_packages_dir():
    suffixes = ("python{}.{}/dist-packages".format(sys.version_info[0], sys.version_info[1]),
                "python{}.{}/site-packages".format(sys.version_info[0], sys.version_info[1]))
    site_packages_dirs = [p for p in sys.path if p.endswith(suffixes)]

    if len(site_packages_dirs) != 1:
        raise Exception(
            "Cannot determine unique site-package dir with suffix '{}'! Candidates {} remaining from {}".format(
                suffixes, site_packages_dirs, sys.path))

    return site_packages_dirs[0]


def get_python_packages(p_main_setup_module, p_arguments, p_include_contrib_packages=True):
    """
        Return tuples describing name and path details of the python packages used for the application.
        
        @return Array of tuples containing
            * 0: path to the package source parent dir
            * 1: filename of the python pip package (excluding path)
            * 2: module name
            * 3: vars of the package
            * 4: target PyPi repository URL
            * 5: variable name containing token for target PyPi repository
    """

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    if p_arguments.use_dev_dir is not None:
        contrib_dir = os.path.join(p_arguments.use_dev_dir, var["setup"]["contrib_dir"])
        app_dir = p_arguments.use_dev_dir

    else:
        contrib_dir = get_site_packages_dir()
        app_dir = get_site_packages_dir()

    branch = var["setup"].get("GIT_BRANCH")
    branch_target_rep_map = var["setup"]["publish_pypi_package"]

    target_rep = None
    target_rep_token_env_name = None

    if isinstance(branch_target_rep_map, dict) and branch is not None:
        target_rep_map_entry = branch_target_rep_map.get(branch)

        if target_rep_map_entry is not None:
            target_rep = target_rep_map_entry[0]
            target_rep_token_env_name = target_rep_map_entry[1]

    if target_rep is None:
        target_rep = DEFAULT_PYPI_REPOSITORY

    if target_rep_token_env_name is None:
        target_rep_token_env_name = DEFAULT_PYPI_TOKEN_ENV_NAME

    contributing_setup_modules = load_contributing_setup_modules(p_main_setup_module)

    python_packages = []

    python_packages.append((app_dir, get_python_package_name(p_var=var), var["setup"]["module_name"], var,
                            target_rep, target_rep_token_env_name))

    if p_include_contrib_packages:
        for contributing_setup_module in contributing_setup_modules:
            contrib_var = get_vars(p_setup_params=contributing_setup_module.extended_setup_params)
            module_name = contrib_var["setup"]["module_name"]

            if p_arguments.use_dev_dir is not None:
                include_path = os.path.join(contrib_dir, module_name)

            else:
                include_path = contrib_dir

            python_packages.append((include_path, get_python_package_name(p_var=contrib_var), module_name, contrib_var,
                                    target_rep, target_rep_token_env_name))

    return python_packages


def generate_standard_file(p_main_setup_module, p_template_env, p_file_description,
                           p_output_filename, p_template_name, p_create_directory=False):
    global logger

    fmt = "Generate {file_description} for version {version} of app '{name}'"
    logger.info(fmt.format(file_description=p_file_description, **p_main_setup_module.extended_setup_params), )

    template = p_template_env.get_template(p_template_name)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(var=get_vars(p_setup_params=p_main_setup_module.extended_setup_params))

    output_file_path = p_output_filename.format(**(var["setup"]))

    filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    if p_create_directory:
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok=True)

    with open(filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote {file_description} file '{filename}'"
    logger.info(fmt.format(filename=filename, file_description=p_file_description))


def generate_git_python_file(p_main_setup_module, p_template_env):
    generate_standard_file(p_main_setup_module=p_main_setup_module, p_template_env=p_template_env,
                           p_file_description="git.py",
                           p_output_filename=GIT_PY_FILE_PATH, p_template_name=GIT_PY_TEMPLATE)


def generate_circle_ci_configuration(p_main_setup_module, p_template_env):
    generate_standard_file(p_main_setup_module=p_main_setup_module, p_template_env=p_template_env,
                           p_file_description="Circle CI configuration",
                           p_output_filename=CIRCLE_CI_FILE, p_template_name=CIRCLE_CI_TEMPLATE,
                           p_create_directory=True)


def generate_gitlab_ci_configuration(p_main_setup_module, p_template_env):
    generate_standard_file(p_main_setup_module=p_main_setup_module, p_template_env=p_template_env,
                           p_file_description="GitLab CI configuration",
                           p_output_filename=GITLAB_CI_FILE, p_template_name=GITLAB_CI_TEMPLATE)


def generate_codacy_configuration(p_main_setup_module, p_template_env):
    generate_standard_file(p_main_setup_module=p_main_setup_module, p_template_env=p_template_env,
                           p_file_description="Codacy configuration",
                           p_output_filename=CODACY_FILE_PATH, p_template_name=CODACY_TEMPLATE)


def generate_debian_control(p_main_setup_module, p_template_env):
    global logger

    fmt = "Generate Debian control file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(DEBIAN_CONTROL_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(var=var, depends=var["setup"]["install_requires"])

    output_file_path = DEBIAN_CONTROL_FILE_PATH.format(**(var["setup"]))

    debian_control_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(debian_control_filename), mode=0o777, exist_ok=True)

    with open(debian_control_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote Debian control file to '{filename}'"
    logger.info(fmt.format(filename=debian_control_filename))


def generate_debian_postinst(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate Debian post installation file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(DEBIAN_POSTINST_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(
        var=var,
        generic_script=False,
        user_group_mappings=var["setup"]["user_group_mappings"],
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments)
    )

    output_file_path = DEBIAN_POSTINST_FILE_PATH.format(**(var["setup"]))

    debian_postinst_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(debian_postinst_filename), mode=0o777, exist_ok=True)

    with open(debian_postinst_filename, "w") as f:
        f.write(output_text)

    os.chmod(debian_postinst_filename,
             stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP | stat.S_IROTH | stat.S_IXOTH)

    fmt = "Wrote Debian post installation file to '{filename}'"
    logger.info(fmt.format(filename=debian_postinst_filename))


def generate_generic_installation_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate generic installation file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(GENERIC_INSTALLATION_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(
        var=var,
        generic_script=True,
        user_group_mappings=var["setup"]["user_group_mappings"],
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments)
    )

    output_file_path = GENERIC_INSTALLATION_SCRIPT_FILE_PATH.format(**(var["setup"]))

    debian_postinst_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(debian_postinst_filename), mode=0o777, exist_ok=True)

    with open(debian_postinst_filename, "w") as f:
        f.write(output_text)

    os.chmod(debian_postinst_filename,
             stat.S_IRUSR | stat.S_IXUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP | stat.S_IROTH | stat.S_IXOTH)

    fmt = "Wrote generic installation script to '{filename}'"
    logger.info(fmt.format(filename=debian_postinst_filename))


def generate_pycoveragerc(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate pycoverage configuration file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(PYCOVERAGE_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments,
                                            p_include_contrib_packages=False)
    )

    output_file_path = PYCOVERAGE_FILE_PATH.format(**(var["setup"]))

    if p_arguments.run_dir is not None:
        run_dir = p_arguments.run_dir

    else:
        run_dir = get_module_dir(p_module=p_main_setup_module)

    pycoveragerc_filename = os.path.join(run_dir, output_file_path)

    with open(pycoveragerc_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote pycoverage configuration file to '{filename}'"
    logger.info(fmt.format(filename=pycoveragerc_filename))


def generate_make_debian_package(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate make_debian_package.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(MAKE_DEBIAN_PACKAGE_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments)
    )

    output_file_path = MAKE_DEBIAN_PACKAGE_SCRIPT_FILE_PATH.format(**(var["setup"]))

    make_debian_package_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(make_debian_package_script_filename), mode=0o777, exist_ok=True)

    with open(make_debian_package_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote make_debian_package.sh script file to '{filename}'"
    logger.info(fmt.format(filename=make_debian_package_script_filename))

    os.chmod(make_debian_package_script_filename,
             stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def generate_build_docker_image_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate build_docker_images.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(BUILD_DOCKER_IMAGE_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments)
    )

    output_file_path = BUILD_DOCKER_IMAGE_SCRIPT_FILE_PATH.format(**(var["setup"]))

    build_docker_image_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(build_docker_image_script_filename), mode=0o777, exist_ok=True)

    with open(build_docker_image_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote build_docker_image.sh script file to '{filename}'"
    logger.info(fmt.format(filename=build_docker_image_script_filename))

    os.chmod(build_docker_image_script_filename,
             stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def generate_install_debian_package_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate install-debian-package.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(INSTALL_DEBIAN_PACKAGE_SCRIPT_TEMPLATE)
    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)
    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments)
    )
    output_file_path = INSTALL_DEBIAN_PACKAGE_SCRIPT_FILE_PATH.format(**(var["setup"]))
    install_and_test_debian_package_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module),
                                                                   output_file_path)
    os.makedirs(os.path.dirname(install_and_test_debian_package_script_filename), mode=0o777, exist_ok=True)

    with open(install_and_test_debian_package_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote install-debian-package.sh script file to '{filename}'"
    logger.info(fmt.format(filename=install_and_test_debian_package_script_filename))

    os.chmod(install_and_test_debian_package_script_filename,
             stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def generate_install_pypi_package_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate install-pypi-package.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(INSTALL_PYPI_PACKAGE_SCRIPT_TEMPLATE)
    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)
    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments)
    )
    output_file_path = INSTALL_PYPI_PACKAGE_SCRIPT_FILE_PATH.format(**(var["setup"]))
    install_and_test_pypi_package_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module),
                                                                 output_file_path)
    os.makedirs(os.path.dirname(install_and_test_pypi_package_script_filename), mode=0o777, exist_ok=True)

    with open(install_and_test_pypi_package_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote install-pypi-package.sh script file to '{filename}'"
    logger.info(fmt.format(filename=install_and_test_pypi_package_script_filename))

    os.chmod(install_and_test_pypi_package_script_filename,
             stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def generate_test_app_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate test-app.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(TEST_APP_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments),
        arguments=p_arguments,
        site_packages_dir=get_site_packages_dir()
    )

    output_file_path = TEST_APP_SCRIPT_FILE_PATH.format(**(var["setup"]))

    test_app_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(test_app_script_filename), mode=0o777, exist_ok=True)

    with open(test_app_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote test-app.sh script file to '{filename}'"
    logger.info(fmt.format(filename=test_app_script_filename))

    os.chmod(test_app_script_filename, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)

def generate_analyze_app_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate analyze-app.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(ANALYZE_APP_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments),
        arguments=p_arguments,
        site_packages_dir=get_site_packages_dir()
    )

    output_file_path = ANALYZE_APP_SCRIPT_FILE_PATH.format(**(var["setup"]))

    analyze_app_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(analyze_app_script_filename), mode=0o777, exist_ok=True)

    with open(analyze_app_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote analyze-app.sh script file to '{filename}'"
    logger.info(fmt.format(filename=analyze_app_script_filename))

    os.chmod(analyze_app_script_filename, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def generate_publish_debian_package_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate publish-debian-package.template.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(PUBLISH_DEBIAN_PACKAGE_SCRIPT_TEMPLATE)
    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)
    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments),
        arguments=p_arguments,
        site_packages_dir=get_site_packages_dir()
    )
    output_file_path = PUBLISH_DEBIAN_PACKAGE_SCRIPT_FILE_PATH.format(**(var["setup"]))
    publish_debian_package_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module),
                                                          output_file_path)
    os.makedirs(os.path.dirname(publish_debian_package_script_filename), mode=0o777, exist_ok=True)

    with open(publish_debian_package_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote publish_debian_package.sh script file to '{filename}'"
    logger.info(fmt.format(filename=publish_debian_package_script_filename))

    os.chmod(publish_debian_package_script_filename,
             stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def generate_publish_pypi_package_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate publish-pypi-package.template.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.extended_setup_params))

    template = p_template_env.get_template(PUBLISH_PYPI_PACKAGE_SCRIPT_TEMPLATE)
    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)
    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments,
                                            p_include_contrib_packages=False),
        arguments=p_arguments,
        site_packages_dir=get_site_packages_dir()
    )
    output_file_path = PUBLISH_PYPI_PACKAGE_SCRIPT_FILE_PATH.format(**(var["setup"]))
    publish_pypi_package_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)
    os.makedirs(os.path.dirname(publish_pypi_package_script_filename), mode=0o777, exist_ok=True)

    with open(publish_pypi_package_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote publish_pypi_package.sh script file to '{filename}'"
    logger.info(fmt.format(filename=publish_pypi_package_script_filename))

    os.chmod(publish_pypi_package_script_filename,
             stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def output_beacon(status):
    global logger

    done = False
    count = 0

    while not status.done:
        time.sleep(1)
        count += 1

        if count % BEACON_INTERVAL == 0:
            fmt = "Beacon: waited for another {sec} seconds..."
            logger.info(fmt.format(sec=BEACON_INTERVAL))


def execute_generated_script(p_main_setup_module, p_script_file_path_pattern):
    var = get_vars(p_setup_params=p_main_setup_module.extended_setup_params)

    output_file_path = p_script_file_path_pattern.format(**(var["setup"]))

    script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    timeout = p_main_setup_module.extended_setup_params.get("script_timeout")

    fmt = "<<<<< START script {filename} (timeout={timeout}[sec])..."
    logger.info(fmt.format(filename=script_filename, timeout=timeout))

    extended_env = os.environ.copy()
    extended_env.update(get_predefined_environment_variables())

    expand_vars(extended_env)
    thread = None
    status = None

    try:
        status = tools.SimpleStatus()
        thread = tools.start_simple_thread(output_beacon, status)

        process = subprocess.Popen(script_filename, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   env=extended_env, bufsize=1, universal_newlines=True)

        msg = "[STDOUT/STDERR] {line}"

        for output in iter(process.stdout.readline, ""):
            for line in output.split("\n"):
                if line != '':
                    logger.info(msg.format(line=line))

        process.communicate(timeout=5)
        exit_code = process.returncode


    except subprocess.CalledProcessError as e:
        exit_code = e.returncode
        fmt = "Exception CalledProcessError in subprocess! stdout='{stdout}' stderr='{stderr}'"
        logger.error(fmt.format(stdout=e.output, stderr=e.stderr))

    except Exception as e:
        exit_code = -1
        msg = "General exception '{exception}' in subprocess!"
        logger.error(msg.format(exception=str(e)))

    finally:

        if status is not None:
            status.done = True

        if thread is not None:
            thread.join()


    msg = ">>>>> END script {filename} ..."
    logger.info(msg.format(filename=script_filename))

    if exit_code != 0:
        raise exceptions.ScriptExecutionError(p_script_name=script_filename, p_exit_code=exit_code)


def execute_make_debian_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=MAKE_DEBIAN_PACKAGE_SCRIPT_FILE_PATH)


def execute_build_docker_image_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=BUILD_DOCKER_IMAGE_SCRIPT_FILE_PATH)


def execute_install_debian_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=INSTALL_DEBIAN_PACKAGE_SCRIPT_FILE_PATH)


def execute_install_pypi_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=INSTALL_PYPI_PACKAGE_SCRIPT_FILE_PATH)


def execute_publish_debian_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=PUBLISH_DEBIAN_PACKAGE_SCRIPT_FILE_PATH)


def execute_publish_pypi_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=PUBLISH_PYPI_PACKAGE_SCRIPT_FILE_PATH)


def execute_test_app_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=TEST_APP_SCRIPT_FILE_PATH)

def execute_analyze_app_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=ANALYZE_APP_SCRIPT_FILE_PATH)

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-stage', dest='execute_stage', default=None,
                        help='execute CI stage',
                        choices=[STAGE_BUILD_PACKAGE,
                                 STAGE_BUILD_DOCKER_IMAGES,
                                 STAGE_PUBLISH_PACKAGE,
                                 STAGE_PUBLISH_PYPI_PACKAGE,
                                 STAGE_INSTALL,
                                 STAGE_INSTALL_PYPI_PACKAGE,
                                 STAGE_TEST,
                                 STAGE_ANALYZE,
                                 STAGE_TEARDOWN,
                                 STAGE_PREPARE])
    parser.add_argument('--run-dir', dest='run_dir', default=None)
    parser.add_argument('--use-dev-dir', dest='use_dev_dir', default=None)
    return parser


def main(p_main_module_dir):
    global logger

    exit_code = 0

    try:
        log_handling.start_logging()

        logger = log_handling.get_logger(__name__)

        parser = get_parser()

        arguments = parser.parse_args()

        main_setup_module = load_setup_module(p_dir=p_main_module_dir, p_module_name="setup")

        template_loader = jinja2.PackageLoader(python_base_app.__name__)
        template_env = jinja2.Environment(loader=template_loader)

        var = get_vars(p_setup_params=main_setup_module.extended_setup_params)

        if arguments.execute_stage == STAGE_BUILD_PACKAGE:
            if var["setup"]["build_debian_package"]:
                generate_debian_control(p_main_setup_module=main_setup_module, p_template_env=template_env)
                generate_debian_postinst(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                         p_arguments=arguments)
            generate_make_debian_package(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                         p_arguments=arguments)
            execute_make_debian_package_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_PUBLISH_PACKAGE:
            generate_publish_debian_package_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                                   p_arguments=arguments)
            execute_publish_debian_package_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_PUBLISH_PYPI_PACKAGE:
            generate_publish_pypi_package_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                                 p_arguments=arguments)
            execute_publish_pypi_package_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_BUILD_DOCKER_IMAGES:
            generate_build_docker_image_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                               p_arguments=arguments)
            execute_build_docker_image_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_INSTALL:
            generate_install_debian_package_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                                   p_arguments=arguments)
            execute_install_debian_package_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_INSTALL_PYPI_PACKAGE:

            generate_install_pypi_package_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                                 p_arguments=arguments)
            execute_install_pypi_package_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_TEST:
            generate_test_app_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                     p_arguments=arguments)
            generate_pycoveragerc(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                  p_arguments=arguments)
            execute_test_app_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_ANALYZE:
            generate_analyze_app_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                     p_arguments=arguments)
            execute_analyze_app_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_PREPARE:
            generate_gitlab_ci_configuration(p_main_setup_module=main_setup_module, p_template_env=template_env)
            generate_circle_ci_configuration(p_main_setup_module=main_setup_module, p_template_env=template_env)
            generate_codacy_configuration(p_main_setup_module=main_setup_module, p_template_env=template_env)
            generate_git_python_file(p_main_setup_module=main_setup_module, p_template_env=template_env)

            var = get_vars(p_setup_params=main_setup_module.extended_setup_params)

            if var["setup"]["generate_generic_install"]:
                generate_generic_installation_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                                     p_arguments=arguments)

        else:
            msg = "No stage selected -> nothing to do!"
            logger.warn(msg)

    except exceptions.ScriptExecutionError as e:
        fmt = "Execution of script {script_name} failed with exit code {exit_code}"
        logger.error(fmt.format(script_name=e.script_name, exit_code=e.exit_code))
        exit_code = 1

    except KeyError as e:
        fmt = "Exception of type {type}: {msg}"
        logger.exception(fmt.format(type=type(e), msg=str(e)))
        exit_code = 2

    except Exception as e:
        fmt = "General exception of type {type}: {msg}"
        logger.error(fmt.format(type=type(e), msg=str(e)))
        exit_code = 2

    fmt = "Exiting with code {exit_code}"
    logger.info(fmt.format(exit_code=exit_code))

    return exit_code
