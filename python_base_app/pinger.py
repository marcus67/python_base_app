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

import requests

from python_base_app import configuration
from python_base_app import log_handling
from python_base_app import tools

SECTION_NAME = "Pinger"

URL_SEPERATOR = ","

DEFAULT_PING_PORT = 6666

if tools.is_mac_os():
    DEFAULT_PING_COMMAND = "/sbin/ping"
    DEFAULT_PING_WAIT_OPTION = "-W"

else:
    DEFAULT_PING_COMMAND = "/bin/ping"
    DEFAULT_PING_WAIT_OPTION = "-w"

# MacOS: round-trip min/avg/max/stddev = 0.043/0.043/0.043/0.000 ms
# Linux: rtt min/avg/max/mdev = 0.043/0.043/0.043/0.000 ms

DEFAULT_PING_RESULT_REGEX = r"(rtt|round-trip) min/avg/max/(mdev|stddev) = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms"
DEFAULT_PING_TIMEOUT_IN_SECONDS = 5


class PingerConfigModel(configuration.ConfigModel):

    def is_active(self):
        return True

    def __init__(self):
        super().__init__(p_section_name=SECTION_NAME)

        self.ping_command = DEFAULT_PING_COMMAND
        self.ping_result_regex = DEFAULT_PING_RESULT_REGEX
        self.ping_wait_option = DEFAULT_PING_WAIT_OPTION


class Pinger(object):

    def __init__(self, p_default_port=None, p_config=None):
        if p_config is None:
            p_config = PingerConfigModel()

        self._config = p_config
        self._default_port = p_default_port
        self._logger = log_handling.get_logger(self.__class__.__name__)

        try:
            self.ping_result_regex = re.compile(self._config.ping_result_regex)

        except Exception:
            fmt = "Invalid regular expression '{regex}' in [{section}]ping_result_regex"
            raise configuration.ConfigurationException(
                fmt.format(regex=self._config.ping_result_regex, section=SECTION_NAME))

    def is_valid_ping(self, p_host):

        if URL_SEPERATOR in p_host:
            first_url = p_host[:p_host.index(URL_SEPERATOR)]
            return tools.is_valid_dns_name(first_url)

        else:
            return tools.is_valid_dns_name(p_dns_name=p_host)

    def ping(self, p_host, p_default_port=None):

        if p_default_port is None:
            p_default_port = self._default_port

        if URL_SEPERATOR in p_host:
            return self.remote_ping(p_url=p_host, p_default_port=p_default_port)

        else:
            return self.local_ping(p_host=p_host)

    def remote_ping(self, p_url, p_default_port, p_default_timeout=DEFAULT_PING_TIMEOUT_IN_SECONDS):

        if not URL_SEPERATOR in p_url:
            msg = "No URL separator found in '{url}'!"
            raise Exception(msg.format(url=p_url))
        try:

            index = p_url.find(URL_SEPERATOR)
            first_url = p_url[:index]
            remaining_url = p_url[index + 1:]

            host, port = tools.split_host_url(p_url=first_url, p_default_port_number=p_default_port)

            url = "http://{host}:{port}/api/ping?host={remaining_url}".format(
                host=host,
                port=port,
                remaining_url=remaining_url
            )

            r = requests.get(url, timeout=p_default_timeout)
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

        fmt = "{ping_command} {w_option} 1 {c_option} {host}"
        raw_command = fmt.format(ping_command=self._config.ping_command,
                                 # Ping command count option as function of OS
                                 c_option='-n 1' if tools.is_windows() else '-c 1',
                                 w_option=self._config.ping_wait_option,
                                 host=shlex.quote(p_host))

        command = shlex.split(raw_command)
        delay = None

        fmt = "Executing command {cmd} in Popen"
        self._logger.debug(fmt.format(cmd=command))

        proc = subprocess.Popen(command, stdout=subprocess.PIPE)

        for line in proc.stdout:
            result = self.ping_result_regex.match(line.decode("UTF-8"))

            if result:
                delay = float(result.group(3))
                break

        fmt = "Host {host} is {status}"
        self._logger.debug(
            fmt.format(host=p_host, status="responding (%.1f ms)" % delay if delay is not None else "down"))

        return delay
