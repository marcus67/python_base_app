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
import copy
import os
import os.path
import stat
import subprocess
import sys

import jinja2

import python_base_app
from python_base_app import exceptions
from python_base_app import log_handling

MODULE_NAME = "base_ci_toolbox"

STAGE_BUILD_PACKAGE = "BUILD"
STAGE_INSTALL = "INSTALL"
STAGE_PUBLISH_PACKAGE = "PUBLISH-PACKAGE"
STAGE_TEST = "TEST"
STAGE_TEARDOWN = "TEARDOWN"
STAGE_PREPARE = "PREPARE"

GITLAB_CI_FILE = '.gitlab-ci.yml'
GITLAB_CI_TEMPLATE = 'gitlab-ci.template.yml'

CIRCLE_CI_FILE = '.circleci/config.yml'
CIRCLE_CI_TEMPLATE = 'circle-ci.template.yml'

PYCOVERAGE_FILE_PATH = '.coveragerc'
PYCOVERAGE_TEMPLATE = 'coveragerc.template'

DEBIAN_CONTROL_FILE_PATH = '{debian_build_dir}/DEBIAN/control'
DEBIAN_CONTROL_TEMPLATE = 'debian_control.template.conf'

DEBIAN_POSTINST_FILE_PATH = '{debian_build_dir}/DEBIAN/postinst'
DEBIAN_POSTINST_TEMPLATE = 'debian_postinst.template.sh'

MAKE_DEBIAN_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/make-debian-package.sh'
MAKE_DEBIAN_PACKAGE_SCRIPT_TEMPLATE = 'make-debian-package.template.sh'

INSTALL_DEBIAN_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/install-debian-package.sh'
INSTALL_DEBIAN_PACKAGE_SCRIPT_TEMPLATE = 'install-debian-package.template.sh'

PUBLISH_DEBIAN_PACKAGE_SCRIPT_FILE_PATH = '{bin_dir}/publish-debian-package.sh'
PUBLISH_DEBIAN_PACKAGE_SCRIPT_TEMPLATE = 'publish-debian-package.template.sh'

TEST_APP_SCRIPT_FILE_PATH = '{bin_dir}/test-app.sh'
TEST_APP_SCRIPT_TEMPLATE = 'test-app.template.sh'

default_setup = {
    "docker_image_make_package": "accso/docker-python-app:latest",
    "docker_image_test": "accso/docker-python-app:latest",
    "ci_toolbox_script": "ci_toolbox.py",
    "ci_stage_build_package": STAGE_BUILD_PACKAGE,
    "ci_stage_install": STAGE_INSTALL,
    "ci_stage_test": STAGE_TEST,
    "ci_stage_teardown": STAGE_TEARDOWN,
    "ci_stage_publish_package": STAGE_PUBLISH_PACKAGE,
    "require_teardown": False,
    "bin_dir": "bin",
    "test_dir": "test",
    "run_test_suite": "run_test_suite.py",
    "contrib_dir": "contrib",
    "rel_tmp_dir": "tmp",
    "rel_etc_dir": "etc/{name}",
    "rel_log_dir": "var/log/{name}",
    "rel_spool_dir": "var/spool/{name}",
    "rel_systemd_dir": "lib/systemd/system",
    "rel_sudoers_dir": "etc/sudoers.d",
    "git_metadata_file": "{module_name}/git_metadata.py",
    "user": "{name}",
    "group": "{name}",
    "user_group_mappings": [],
    "create_usr": False,
    "create_group": False,
    "deploy_systemd_service": False,
    "deploy_sudoers_file": False,
    "version": "0.1",
    "debian_build_dir": "debian",
    "debian_package_name": "{name}",
    "debian_package_revision": "1",
    "debian_package_section": "base",
    "debian_package_priority": "optional",
    "debian_package_architecture": "amd64",
    "debian_dependencies": [],
    "debian_extra_files" : [],
    "install_requires": [],
    "contributing_setups": [],
    "publish_debian_package": False
}

logger = None


def get_module_dir(p_module):
    return os.path.dirname(p_module.__file__)


def get_python_package_name(p_var):
    return "{name}-{version}.tar.gz".format(**(p_var["setup"]))


def get_vars(p_setup_params):
    setup = copy.copy(default_setup)
    setup.update(p_setup_params)

    setup["module_name"] = setup["name"].replace("-", "_")

    while True:

        change_done = False

        for (key, value) in setup.items():
            if isinstance(value, str):
                new_value = value.format(**setup)

                if new_value != value:
                    change_done = True
                    setup[key] = new_value

        if not change_done:
            break

    return {"setup": setup}


def load_setup_module(p_dir, p_module_name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(p_module_name, "{dir}/setup.py".format(dir=p_dir))
    setup_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(setup_module)
    return setup_module


def load_contributing_setup_modules(p_main_setup_module):
    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

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
            * the path to the package source parent dir
            * the filename of the python pip package (excluding path)
            * the module name
            * the vars of the package
    """

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

    if p_arguments.use_dev_dir is not None:
        contrib_dir = os.path.join(p_arguments.use_dev_dir, var["setup"]["contrib_dir"])
        app_dir = p_arguments.use_dev_dir

    else:
        contrib_dir = get_site_packages_dir()
        app_dir = get_site_packages_dir()

    contributing_setup_modules = load_contributing_setup_modules(p_main_setup_module)

    python_packages = []

    if p_include_contrib_packages:
        for contributing_setup_module in contributing_setup_modules:
            contrib_var = get_vars(p_setup_params=contributing_setup_module.setup_params)
            module_name = contrib_var["setup"]["module_name"]

            if p_arguments.use_dev_dir is not None:
                include_path = os.path.join(contrib_dir, module_name)

            else:
                include_path = contrib_dir

            python_packages.append((include_path, get_python_package_name(p_var=contrib_var), module_name, contrib_var))

    python_packages.append((app_dir, get_python_package_name(p_var=var), var["setup"]["module_name"], var))

    return python_packages


def generate_gitlab_ci_configuration(p_main_setup_module, p_template_env):
    global logger

    fmt = "Generate GitLab CI configuration for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(GITLAB_CI_TEMPLATE)

    output_text = template.render(var=get_vars(p_setup_params=p_main_setup_module.setup_params))

    gitlab_ci_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), GITLAB_CI_FILE)

    with open(gitlab_ci_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote CI configuration to file '{filename}'"
    logger.info(fmt.format(filename=gitlab_ci_filename))


def generate_circle_ci_configuration(p_main_setup_module, p_template_env):
    global logger

    fmt = "Generate Circle CI configuration for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(CIRCLE_CI_TEMPLATE)

    output_text = template.render(var=get_vars(p_setup_params=p_main_setup_module.setup_params))

    gitlab_ci_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), CIRCLE_CI_FILE)

    directory = os.path.dirname(gitlab_ci_filename)

    os.makedirs(directory, exist_ok=True)

    with open(gitlab_ci_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote Circle CI configuration to file '{filename}'"
    logger.info(fmt.format(filename=gitlab_ci_filename))


def generate_debian_control(p_main_setup_module, p_template_env):
    global logger

    fmt = "Generate Debian control file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(DEBIAN_CONTROL_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

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
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(DEBIAN_POSTINST_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

    output_text = template.render(
        var=var,
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


def generate_pycoveragerc(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate pycoverage configuration file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(PYCOVERAGE_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

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
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(MAKE_DEBIAN_PACKAGE_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

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


def generate_install_debian_package_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate install-debian-package.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(INSTALL_DEBIAN_PACKAGE_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

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


def generate_test_app_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate test-app.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(TEST_APP_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

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


def generate_publish_debian_package_script(p_main_setup_module, p_template_env, p_arguments):
    global logger

    fmt = "Generate publish-debian-package.template.sh script file for version {version} of app '{name}'"
    logger.info(fmt.format(**p_main_setup_module.setup_params))

    template = p_template_env.get_template(PUBLISH_DEBIAN_PACKAGE_SCRIPT_TEMPLATE)

    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

    output_text = template.render(
        var=var,
        python_packages=get_python_packages(p_main_setup_module=p_main_setup_module, p_arguments=p_arguments),
        arguments=p_arguments,
        site_packages_dir=get_site_packages_dir()
    )

    output_file_path = PUBLISH_DEBIAN_PACKAGE_SCRIPT_FILE_PATH.format(**(var["setup"]))

    publish_debian_package_script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    os.makedirs(os.path.dirname(publish_debian_package_script_filename), mode=0o777, exist_ok=True)

    with open(publish_debian_package_script_filename, "w") as f:
        f.write(output_text)

    fmt = "Wrote publish_debian_package.sh script file to '{filename}'"
    logger.info(fmt.format(filename=publish_debian_package_script_filename))

    os.chmod(publish_debian_package_script_filename, stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXGRP | stat.S_IRGRP)


def execute_generated_script(p_main_setup_module, p_script_file_path_pattern):
    var = get_vars(p_setup_params=p_main_setup_module.setup_params)

    output_file_path = p_script_file_path_pattern.format(**(var["setup"]))

    script_filename = os.path.join(get_module_dir(p_module=p_main_setup_module), output_file_path)

    fmt = "<<<<< START script {filename} ..."
    logger.info(fmt.format(filename=script_filename))

    popen = subprocess.Popen(script_filename, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = popen.communicate()
    exit_code = popen.returncode
    msg = "[STDOUT] {line}"

    for line in stdout.decode("utf-8").split("\n"):
        if line != '':
            logger.info(msg.format(line=line))

    msg = "[STDERR] {line}"

    for line in stderr.decode("utf-8").split("\n"):
        if line != '':
            logger.error(msg.format(line=line))

    msg = ">>>>> END script {filename} ..."
    logger.info(msg.format(filename=script_filename))

    if exit_code != 0:
        raise exceptions.ScriptExecutionError(p_script_name=script_filename, p_exit_code=exit_code)


def execute_make_debian_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=MAKE_DEBIAN_PACKAGE_SCRIPT_FILE_PATH)


def execute_install_debian_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=INSTALL_DEBIAN_PACKAGE_SCRIPT_FILE_PATH)

def execute_publish_debian_package_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=PUBLISH_DEBIAN_PACKAGE_SCRIPT_FILE_PATH)

def execute_test_app_script(p_main_setup_module):
    execute_generated_script(p_main_setup_module=p_main_setup_module,
                             p_script_file_path_pattern=TEST_APP_SCRIPT_FILE_PATH)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute-stage', dest='execute_stage', default=None,
                        help='execute CI stage',
                        choices=[STAGE_BUILD_PACKAGE, STAGE_PUBLISH_PACKAGE, STAGE_INSTALL,
                                 STAGE_TEST, STAGE_TEARDOWN, STAGE_PREPARE])
    parser.add_argument('--run-dir', dest='run_dir', default=None)
    parser.add_argument('--use-dev-dir', dest='use_dev_dir', default=None)
    return parser


def main(p_main_module_dir):
    global logger

    try:
        log_handling.start_logging()

        logger = log_handling.get_logger(__name__)

        parser = get_parser()

        arguments = parser.parse_args()

        main_setup_module = load_setup_module(p_dir=p_main_module_dir, p_module_name="setup")

        template_loader = jinja2.PackageLoader(python_base_app.__name__)
        template_env = jinja2.Environment(loader=template_loader)

        if arguments.execute_stage == STAGE_BUILD_PACKAGE:
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

        elif arguments.execute_stage == STAGE_INSTALL:
            generate_install_debian_package_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                                   p_arguments=arguments)
            execute_install_debian_package_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_TEST:
            generate_test_app_script(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                     p_arguments=arguments)
            generate_pycoveragerc(p_main_setup_module=main_setup_module, p_template_env=template_env,
                                  p_arguments=arguments)
            execute_test_app_script(p_main_setup_module=main_setup_module)

        elif arguments.execute_stage == STAGE_PREPARE:
            generate_gitlab_ci_configuration(p_main_setup_module=main_setup_module, p_template_env=template_env)
            generate_circle_ci_configuration(p_main_setup_module=main_setup_module, p_template_env=template_env)

        else:
            msg = "No stage selected -> nothing to do!"
            logger.warn(msg)

    except exceptions.ScriptExecutionError as e:
        fmt = "Execution of script {script_name} failed with exit code {exit_code}"
        logger.error(fmt.format(script_name=e.script_name, exit_code=e.exit_code))
        return 1

    return 0
