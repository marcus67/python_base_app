# -*- coding: utf-8 -*-

#    Copyright (C) 2019-2021  Marcus Rickert
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

import datetime
import inspect
import io
import json
import os
import platform
import pwd
import re
import socket
import stat
import sys
import threading
import time
import traceback
import urllib.parse
from os.path import dirname

from python_base_app import configuration
from python_base_app import exceptions
from python_base_app import log_handling

FORMAT_TIME_WITH_SECONDS = "%H:%M:%S"
FORMAT_TIME = "%H:%M"
FORMAT_DATE = "%Y-%m-%d (%a)"
FORMAT_SHORT_DATE = "%A"
FORMAT_SIMPLE_DATE = "%Y-%m-%d"
FORMAT_DATETIME = "%Y-%m-%d %H:%M:%S"
FORMAT_DURATION_WITH_SECONDS = "%dh%02dm%02ds"
FORMAT_DURATION = "%dh%02dm"

FORMAT_JSON_DATETIME = "%Y-%m-%d %H:%M:%S"

REGEX_DURATION = re.compile("^ *(([0-9]+) *[h|H])? *(([0-9]+) *[m|M])? *(([0-9]+) *[s|S])? *$")
REGEX_TIME = re.compile("^ *([0-9]+)( *: *([0-9]+))?( *: *([0-9]+))? *$")

EMPTY_DURATION = "-"
EMPTY_TIME = "-"

PLATFORM_NAME_WINDOWS = 'windows'
PLATFORM_NAME_MAC_OS = "darwin"

PASSWORD_PATTERNS = ("PASSW", "KENNW", "ACCESS", "SECRET")
PROTECTED_PASSWORD_VALUE = "[HID" "DEN]"  # trick Codacy

PORT_NUMBER_SEPERATOR = ":"


# Dummy function to trigger extraction by pybabel...
def _(x):
    return x


class SimpleStatus(object):

    def __init__(self):
        self.done = False


def int_to_string(p_integer):
    if p_integer is None:
        return "[None]"

    else:
        return str(p_integer)


def is_windows():
    return platform.system().lower() == PLATFORM_NAME_WINDOWS


def is_mac_os():
    return platform.system().lower() == PLATFORM_NAME_MAC_OS


def get_current_time():
    return datetime.datetime.now()


def get_today():
    today = datetime.datetime.now()
    return datetime.datetime(year=today.year, month=today.month, day=today.day)


def get_date_as_string(p_date, p_short=False):
    if p_date is not None:
        if p_short:
            return p_date.strftime(FORMAT_SHORT_DATE)

        else:
            return p_date.strftime(FORMAT_DATE)

    else:
        return "[None]"


def get_simple_date_as_string(p_date):
    if p_date is not None:
        return p_date.strftime(FORMAT_SIMPLE_DATE)

    else:
        return "[None]"


def get_timestamp_as_string(p_timestamp):
    if p_timestamp is not None:
        return p_timestamp.strftime(FORMAT_DATETIME)

    else:
        return "[None]"


def get_time_as_string(p_timestamp, p_include_seconds=True):
    if p_timestamp is not None:
        if p_include_seconds:
            return p_timestamp.strftime(FORMAT_TIME_WITH_SECONDS)

        else:
            return p_timestamp.strftime(FORMAT_TIME)

    else:
        return "[None]"


def get_duration_as_string(p_seconds, p_include_seconds=True):
    if p_seconds is None:
        return "-"

    else:
        hours = int(p_seconds / 3600)
        minutes = int((p_seconds - hours * 3600) / 60)

        if p_include_seconds:
            seconds = int(p_seconds - hours * 3600 - minutes * 60)
            return FORMAT_DURATION_WITH_SECONDS % (hours, minutes, seconds)

        else:
            return FORMAT_DURATION % (hours, minutes)


def is_protected_name(p_name):
    for pattern in PASSWORD_PATTERNS:
        if pattern in p_name.upper():
            return True

    return False


def protect_password_value(p_name, p_value):
    if is_protected_name(p_name=p_name):
        return PROTECTED_PASSWORD_VALUE

    else:
        return p_value


def get_safe_attribute_name(p_string):
    return p_string.replace(":", "_").replace("-", "_")


def convert_query_result_to_json(p_result, p_columns):
    a = []
    for entry in p_result:
        d = {}
        i = 0
        for col in p_columns:
            raw_value = getattr(entry, col)
            if type(raw_value) is datetime.datetime:
                value = raw_value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                value = raw_value
            d[col] = value
            i = i + 1
        a.append(d)

    return json.dumps(a, separators=(',', ':'))


def test_mode(p_filename, p_app_owner, p_executable=False, p_writable=False, p_is_directory=False, p_other_access=True):
    logger = log_handling.get_logger()
    p_filename = os.path.abspath(p_filename)

    if p_is_directory:
        if not os.path.isdir(p_filename):
            raise exceptions.InstallationException("Directory '%s' not found!" % p_filename)

    else:
        if not os.path.isfile(p_filename):
            raise exceptions.InstallationException("File '%s' not found!" % p_filename)

    info = os.stat(p_filename)

    if p_app_owner is not None:
        owner_name = pwd.getpwuid(info.st_uid).pw_name

        if owner_name != p_app_owner:
            raise exceptions.InstallationException(
                "File/directory '%s' must be owned by '%s'!" % (p_filename, p_app_owner))

        logger.info("File/directory '%s' is owned by '%s' -> OK" % (p_filename, p_app_owner))

    if info.st_mode & stat.S_IRUSR == 0:
        raise exceptions.InstallationException("File/directory '%s' must be readable by owner!" % p_filename)

    logger.info("File/directory '%s' must be readable by owner -> OK" % p_filename)

    if p_executable:
        if info.st_mode & stat.S_IXUSR == 0:
            raise exceptions.InstallationException("File/directory '%s' must be executable by owner!" % p_filename)
        logger.info("File/directory '%s' must be executable by owner -> OK" % p_filename)

    if p_writable:
        if info.st_mode & stat.S_IWUSR == 0:
            raise exceptions.InstallationException("File/directory '%s' must be writable by owner!" % p_filename)
        logger.info("File/directory '%s' must be writable by owner -> OK" % p_filename)

    if not p_other_access:
        if info.st_mode & (stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH | stat.S_IXGRP | stat.S_IXOTH) > 0:
            raise exceptions.InstallationException(
                "File/directory '%s' must not be accessible by group or others!" % p_filename)
        logger.info("File/directory '%s' must not be accessible by group or others!" % p_filename)


class ObjectEncoder(json.JSONEncoder):

    def __init__(self, *args, **kwargs):

        super(ObjectEncoder, self).__init__(*args, **kwargs)

    def default(self, obj):

        if type(obj) is datetime.datetime:
            return self.default(obj.strftime(FORMAT_JSON_DATETIME))

        elif hasattr(obj, "to_json"):
            return self.default(obj.to_json())

        elif hasattr(obj, "__dict__"):
            d = dict(
                (key, value)
                for key, value in inspect.getmembers(obj)
                if not key.startswith("__")
                and not inspect.isabstract(value)
                and not inspect.isbuiltin(value)
                and not inspect.isfunction(value)
                and not inspect.isgenerator(value)
                and not inspect.isgeneratorfunction(value)
                and not inspect.ismethod(value)
                and not inspect.ismethoddescriptor(value)
                and not inspect.isroutine(value)
                and not isinstance(value, property)
            )
            return self.default(d)

        return obj


def anonymize_args(p_args):
    new_args = []
    hide = False

    for arg in p_args:
        if is_protected_name(arg):
            new_args.append(arg)
            hide = True
        elif hide:
            new_args.append(PROTECTED_PASSWORD_VALUE)
            hide = False
        else:
            new_args.append(arg)

    return new_args


def anonymize_url(p_url):
    components = urllib.parse.urlparse(p_url)

    if components.password is not None:
        fmt = "{username}:{protected_value}@{hostname}"
        net_location = fmt.format(username=components.username, protected_value=PROTECTED_PASSWORD_VALUE,
                                  hostname=components.hostname)
    else:
        net_location = components.netloc

    return urllib.parse.urlunsplit(
        (
            components.scheme,
            net_location,
            components.path,
            components.params,
            components.query
        ))


def get_package_directory(p_package):
    return dirname(p_package.__file__)


def check_config_value(p_config, p_config_attribute_name):
    if getattr(p_config, p_config_attribute_name) is None:
        raise configuration.ConfigurationException(
            "Setting [%s]%s is missing!" % (p_config.section_name, p_config_attribute_name))


def log_stack_trace(p_logger=None):
    (_type, _value, tb) = sys.exc_info()
    string_buffer = io.StringIO()
    traceback.print_tb(tb=tb, file=string_buffer)

    fmt = "Stack trace = %s" % str(string_buffer.getvalue())

    if p_logger is not None:
        p_logger.error(fmt)
    else:
        sys.stderr.write(fmt)


def handle_fatal_exception(p_exception, p_logger=None):
    if p_logger is not None:
        p_logger.fatal(str(p_exception))

    else:
        sys.stderr.write(str(p_exception))


def objectify_dict(p_dict, p_class, p_attribute_classes=None):
    if p_attribute_classes is None:
        p_attribute_classes = {}

    instance = p_class()

    for attr_name, attr_value in p_dict.items():
        if attr_value is not None and attr_name in p_attribute_classes:
            attr_class = p_attribute_classes[attr_name]

            if attr_class == datetime.datetime:
                attr_value = datetime.datetime.strptime(attr_value, FORMAT_JSON_DATETIME)

        setattr(instance, attr_name, attr_value)

    return instance


def start_simple_thread(method, *args, **kwargs):
    new_thread = threading.Thread(target=method, args=args, kwargs=kwargs)
    new_thread.start()

    return new_thread


def get_string_as_duration(p_string):
    if p_string is None:
        return None

    if p_string.strip() in (EMPTY_DURATION, ''):
        return None

    match = REGEX_DURATION.match(p_string)

    if match is None:
        fmt = _("Use Hh MMm SSs")
        raise configuration.ConfigurationException(fmt.format(string=p_string))

    result = 0

    if match.group(2) is not None:
        result = result + 3600 * int(match.group(2))

    if match.group(4) is not None:
        result = result + 60 * int(match.group(4))

    if match.group(6) is not None:
        result = result + int(match.group(6))

    return result


def get_string_as_time(p_string):
    if p_string is None:
        return None

    if p_string.strip() in (EMPTY_TIME, ''):
        return None

    match = REGEX_TIME.match(p_string)

    if match is None:
        fmt = _("Use HH[:MM[:SS]]")
        raise configuration.ConfigurationException(fmt.format(string=p_string))

    hour = int(match.group(1))

    if match.group(3) is not None:
        minute = int(match.group(3))

    else:
        minute = 0

    if match.group(5) is not None:
        second = int(match.group(5))

    else:
        second = 0

    return datetime.time(hour=hour, minute=minute, second=second)


class TimingContext(object):

    def __init__(self, p_result_handler):
        self._result_handler = p_result_handler

    def __enter__(self):
        self._start = time.time()

    def __exit__(self, a_type, value, a_traceback):
        self._end = time.time()
        self._result_handler(self._end - self._start)


def get_new_object_name(p_name_pattern, p_existing_names):
    an_id = 1
    found = False
    new_name = None

    while not found:
        new_name = p_name_pattern.format(id=an_id)

        if new_name in p_existing_names:
            an_id += 1

        else:
            found = True

    return new_name


def split_host_url(p_url, p_default_port_number):
    index = p_url.find(PORT_NUMBER_SEPERATOR)

    if index >= 0:
        host = p_url[:index]
        port_string = p_url[index + 1:]

        try:
            port_number = int(port_string)

        except Exception:
            msg = "Invalid port number {port}"
            raise ValueError(msg.format(port=port_string))

        if port_number < 1 or port_number > 65535:
            msg = "Port number {port} of ouf range"
            raise ValueError(msg.format(port=port_number))

        return host, port_number

    else:
        return p_url, p_default_port_number


def is_valid_dns_name(p_dns_name):
    try:
        dns_name, port = split_host_url(p_url=p_dns_name, p_default_port_number=1)

    except ValueError:
        return False

    try:
        socket.gethostbyname(dns_name)
        return True

    except socket.gaierror:
        return False


def get_dns_name_by_ip_address(p_ip_address):
    try:
        result = socket.gethostbyaddr(p_ip_address)
        return result[0]

    except Exception:
        return p_ip_address


def objects_are_equal(p_object1: object, p_object2: object, p_logger=None):
    for attr, value1 in p_object1.__dict__.items():
        if not attr.startswith('_') and not callable(value1):
            value2 = getattr(p_object2, attr)

            if value1 is None and value2 is None:
                continue

            if value1 is None and value2 is not None:
                return False

            if value2 is None and value1 is not None:
                return False

            if type(value1) != type(value2):
                if p_logger is not None:
                    msg = "objects_are_equal: attribute type of '{attr}' differs: '{type1}' != '{type2}'"
                    p_logger.error(msg.format(attr=attr, type1=type(value1), type2=type(value2)))

                return False

            if not isinstance(value1, (int, float, complex, datetime.date, datetime.time, str)):
                if not objects_are_equal(p_object1=value1, p_object2=value2, p_logger=p_logger):
                    return False

            elif value1 != value2:
                if p_logger is not None:
                    msg = "objects_are_equal: attribute '{attr}' differs: '{value1}' != '{value2}'"
                    p_logger.error(msg.format(attr=attr, value1=value1, value2=value2))

                return False

    return True


def format_boolean(p_value):
    return _("On") if p_value else _("Off")


def value_or_not_set(p_value):
    if p_value is None:
        return _("Not set")

    else:
        return p_value


def running_in_docker():
    return os.getenv("RUNNING_IN_DOCKER") is not None

def running_in_snap():
    return os.getenv("RUNNING_IN_SNAP") is not None


def copy_attributes(p_from: object, p_to: object, p_only_existing=False) -> None:
    for (key, value) in p_from.__dict__.items():
        if not key.startswith('_'):
            if key in p_to.__dict__ or not p_only_existing:
                setattr(p_to, key, value)


def create_class_instance(p_class, p_initial_values) -> object:
    instance = p_class()
    copy_attributes(p_from=p_initial_values, p_to=instance)
    return instance
