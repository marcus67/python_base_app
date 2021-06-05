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

import os
import tempfile

import sys

import setuptools

from python_base_app import base_ci_toolbox
from python_base_app.test import base_test

SPOOL_DIR = tempfile.gettempdir()
TEXT = "hallo"
LOCALE = "de_DE"

STAGE_PREPARE_FILES = [
    '.circleci/config.yml',
    '.gitlab-ci.yml',
    '.codacy.yml',
    'a_package/git.py'
]

STAGE_PREPARE_DIRS = [
    '.circleci',
]

STAGE_BUILD_FILES = [
    'bin/make-debian-package.sh',
    'a_package/translations/de/LC_MESSAGES/messages.mo',
    'a_package.egg-info/dependency_links.txt',
    'a_package.egg-info/PKG-INFO',
    'a_package.egg-info/requires.txt',
    'a_package.egg-info/SOURCES.txt',
    'a_package.egg-info/top_level.txt',
    'dist/a_package-0.0.1.tar.gz'
]

STAGE_BUILD_DIRS = [
    'bin',
    'dist',
    'a_package.egg-info'
]

STAGE_TEST_FILES = [
    'bin/test-app.sh',
    '.coveragerc',
]

STAGE_TEST_DIRS = [
    'bin'
]

RESOURCE_BASE_PATH = "resources/ci_toolbox"


class TestBaseCiToolbox(base_test.BaseTestCase):

    def get_resource_base_path(self):

        return os.path.join(os.path.dirname(__file__), RESOURCE_BASE_PATH)

    def remove_files(self, p_rel_paths, p_rel_dirs):

        for rel_path in p_rel_paths:
            self.rel_delete_file(rel_path)

        for rel_dir in p_rel_dirs:
            self.rel_delete_dir(rel_dir)

    def rel_test_files(self, p_rel_paths):

        for rel_path in p_rel_paths:
            dir_path = os.path.join(self.get_resource_base_path(), rel_path)

            self.assertTrue(os.path.exists(dir_path), "file {path} exists".format(path=dir_path))

    def rel_delete_dir(self, p_rel_path):
        dir_path = os.path.join(self.get_resource_base_path(), p_rel_path)

        if os.path.exists(dir_path):
            os.rmdir(dir_path)

    def rel_delete_file(self, p_rel_path):
        dir_path = os.path.join(self.get_resource_base_path(), p_rel_path)

        if os.path.exists(dir_path):
            os.unlink(dir_path)

    def test_stage_prepare(self):

        self.remove_files(p_rel_paths=STAGE_PREPARE_FILES, p_rel_dirs=STAGE_PREPARE_DIRS)
        main_module_dir = os.path.join(os.path.dirname(__file__), self.get_resource_base_path())

        sys.argv.extend(['--execute-stage', 'PREPARE'])
        base_ci_toolbox.main(p_main_module_dir=main_module_dir)

        self.rel_test_files(p_rel_paths=STAGE_PREPARE_FILES)

        self.remove_files(p_rel_paths=STAGE_PREPARE_FILES, p_rel_dirs=STAGE_PREPARE_DIRS)

    def test_stage_build(self):

        print("setuptools.version", setuptools.version.__version__)

        self.remove_files(p_rel_paths=STAGE_BUILD_FILES, p_rel_dirs=STAGE_BUILD_DIRS)
        main_module_dir = os.path.join(os.path.dirname(__file__), self.get_resource_base_path())

        sys.argv.extend(['--execute-stage', 'BUILD', '--use-dev-dir', self.get_resource_base_path()])
        base_ci_toolbox.main(p_main_module_dir=main_module_dir)

        self.rel_test_files(p_rel_paths=STAGE_BUILD_FILES)

        self.remove_files(p_rel_paths=STAGE_BUILD_FILES, p_rel_dirs=STAGE_BUILD_DIRS)
