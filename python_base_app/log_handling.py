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

import logging
import logging.handlers
import os
from os.path import join

g_logging_started = False

LOG_BACKUP_COUNT = 10
LOG_MAX_BYTES = 1000000

class LogDataHandler(object):

    def get_log_username(self):
        return None

    def get_log_client_ip(self):
        return None


g_log_data_handler = LogDataHandler()


# Siehe https://docs.python.org/3/howto/logging-cookbook.html#context-info
class LogFilter(logging.Filter):

    def filter(self, record):
        global g_log_data_handler

        username = g_log_data_handler.get_log_username()
        client_ip = g_log_data_handler.get_log_client_ip()

        record.raw_username = username
        record.raw_client_ip = client_ip

        record.username = "login=%s - " % username if username is not None else ""
        record.client_ip = "client-ip=%s - " % client_ip if client_ip is not None else ""
        return True


g_log_filter = LogFilter()


def register_log_data_handler(p_log_data_handler):
    global g_log_data_handler

    g_log_data_handler = p_log_data_handler


def get_log_level_by_name(p_log_level_name):
    return getattr(logging, p_log_level_name, None)


def start_logging(p_log_dir=None, p_log_file=None, p_level=logging.DEBUG, p_use_filter=True):
    global g_logging_started
    global g_log_data_handler
    global g_log_filter

    if (not g_logging_started):

        g_logging_started = True
        logger = get_logger()
        logger.setLevel(p_level)

        if p_log_dir is not None:

            log_filename = join(p_log_dir, p_log_file)
            h = logging.handlers.RotatingFileHandler(log_filename, backupCount=LOG_BACKUP_COUNT, maxBytes=LOG_MAX_BYTES,
                                                     encoding="UTF-8")

        else:

            h = logging.StreamHandler()

        # create formatter and add it to the handlers
        if p_use_filter:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(client_ip)s%(username)s%(message)s')

        else:
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        h.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(h)
        add_default_filter_to_logger(logger)

        fmt = "Started logging in CWD={cwd} using module {module_name}"
        logger.info(fmt.format(cwd=os.getcwd(), module_name=__name__))


def add_default_filter_to_logger(p_logger):
    global g_log_filter

    p_logger.addFilter(g_log_filter)


def set_level(p_log_level):
    msg = "Set logging level to {level}"
    get_logger().info(msg.format(level=p_log_level))

    get_logger().setLevel(get_log_level_by_name(p_log_level_name=p_log_level))

    for h in get_logger().handlers:
        h.setLevel(get_log_level_by_name(p_log_level_name=p_log_level))


def add_default_filter_to_logger_by_name(p_name):
    logger = logging.getLogger(p_name)
    add_default_filter_to_logger(p_logger=logger)


def get_logger(p_name=None):
    logger = logging.getLogger(p_name)
    add_default_filter_to_logger(p_logger=logger)
    return logger


def register_handler(p_log_handler):
    logger = get_logger()
    logger.addHandler(p_log_handler)
