# -*- coding: utf-8 -*-

#    Copyright (C) 2021  Marcus Rickert
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

import re
import shlex
import subprocess
import urllib.parse
import requests

from python_base_app import configuration
from python_base_app import log_handling
from python_base_app import tools

SECTION_NAME = "Pinger"

DEFAULT_PING_COMMAND = "/bin/ping"
DEFAULT_PING_RESULT_REGEX = r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms"


class PingerConfigModel(configuration.ConfigModel):

    def is_active(self):
        return True

    def __init__(self):
        super().__init__(p_section_name=SECTION_NAME)

        self.ping_command = DEFAULT_PING_COMMAND
        self.ping_result_regex = DEFAULT_PING_RESULT_REGEX


class Pinger(object):

    def __init__(self, p_config):
        self._config = p_config
        self._logger = log_handling.get_logger(self.__class__.__name__)

        try:
            self.ping_result_regex = re.compile(self._config.ping_result_regex)

        except Exception:
            fmt = "Invalid regular expression '{regex}' in [{section}]ping_result_regex"
            raise configuration.ConfigurationException(
                fmt.format(regex=self._config.ping_result_regex, section=SECTION_NAME))

    def is_valid_ping(self, p_host):

        if ":" in p_host:

            try:
                parts = urllib.parse.urlparse(p_host)

            except ValueError:
                return False

            return tools.is_valid_dns_name(parts.hostname)

        else:
            return tools.is_valid_dns_name(p_dns_name=p_host)

    def ping(self, p_host):

        if ":" in p_host:
            return self.remote_ping(p_url=p_host)

        else:
            return self.local_ping(p_host=p_host)

    def remote_ping(self, p_url):

        try:
            r = requests.get(p_url)
            delay = float(r.text)

        except:
            return None

        return delay


    # https://stackoverflow.com/questions/2953462/pinging-servers-in-python
    def local_ping(self, p_host):
        """
        Returns True if host (str) responds to a ping request.
        Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
        """

        fmt = "{ping_command} -w 1 {c_option} {host}"
        raw_command = fmt.format(ping_command=self._config.ping_command,
                                 # Ping command count option as function of OS
                                 c_option='-n 1' if tools.is_windows() else '-c 1',
                                 host=shlex.quote(p_host))

        command = shlex.split(raw_command)
        delay = None

        fmt = "Executing command {cmd} in Popen"
        self._logger.debug(fmt.format(cmd=command))

        proc = subprocess.Popen(command, stdout=subprocess.PIPE)

        for line in proc.stdout:
            result = self.ping_result_regex.match(line.decode("UTF-8"))

            if result:
                delay = float(result.group(1))
                break

        fmt = "Host {host} is {status}"
        self._logger.debug(
            fmt.format(host=p_host, status="responding (%.1f ms)" % delay if delay is not None else "down"))

        return delay
