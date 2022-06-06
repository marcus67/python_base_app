# -*- coding: utf-8 -*-

# Copyright (C) 2019-2022  Marcus Rickert
#
# See https://github.com/marcus67/python_base_app
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os.path
import shlex
import subprocess

from python_base_app import configuration
from python_base_app import base_audio_player
from python_base_app import tools

DEFAULT_PLAY_COMMAND_PATTERN = "{binary} {filename}"


class Mpg123AudioPlayer(base_audio_player.BaseAudioPlayer):

    def __init__(self, p_mpg123_binary, p_play_command_pattern=DEFAULT_PLAY_COMMAND_PATTERN):

        super().__init__()
        self._mpg123_binary = p_mpg123_binary
        self._play_command_pattern = p_play_command_pattern

        if not os.path.exists(p_mpg123_binary):
            fmt = "Cannot find mpg123 binary at path '{path}'"
            raise configuration.ConfigurationException(fmt.format(path=p_mpg123_binary))

        fmt = "using audio player '{path}'"
        self._logger.info(fmt.format(path=p_mpg123_binary))

    def play_audio_file(self, p_audio_filename):  # pragma: no cover

        if tools.is_windows():
            binary = '"' + self._mpg123_binary + '"'
            filename = '"' + p_audio_filename + '"'

        else:
            binary = self._mpg123_binary
            filename = p_audio_filename

        play_command = self._play_command_pattern.format(binary=binary, filename=filename)

        msg = f"Executing command '{play_command}'..."

        self._logger.debug(msg)

        cmd_array = shlex.split(play_command)
        subprocess.run(cmd_array)
