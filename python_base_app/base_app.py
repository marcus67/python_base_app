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
import datetime
import heapq
import os
import pathlib
import signal
import time

import flask

from python_base_app import configuration
from python_base_app import daemon
from python_base_app import exceptions
from python_base_app import locale_helper
from python_base_app import log_handling
from python_base_app import settings
from python_base_app import tools

PACKAGE_NAME = "python_base_app"

DEFAULT_DEBUG_MODE = False

DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_SPOOL_BASE_DIR = "/var/spool"
DEFAULT_USER_CONFIG_DIR = ".config"
DEFAULT_CONF_EXTENSION = ".conf"
DEFAULT_LANGUAGES = ['en']
DEFAULT_NO_LOG_FILTER = False

TIME_SLACK = 0.1  # seconds
ETERNITY = 24 * 3600  # seconds
DEFAULT_TASK_INTERVAL = 10  # seconds
DEFAULT_MAXIMUM_TIMER_SLACK = 5  # second
DEFAULT_MINIMUM_DOWNTIME_DURATION = 20  # seconds

CONTRIB_LOG_PATHS = [
    "alembic.runtime.migration"
]

class BaseAppConfigModel(configuration.ConfigModel):

    def __init__(self, p_section_name="BaseApp"):
        super().__init__(p_section_name=p_section_name)

        self.debug_mode = DEFAULT_DEBUG_MODE
        self.log_level = configuration.NONE_STRING
        self.spool_dir = configuration.NONE_STRING
        self.minimum_downtime_duration = DEFAULT_MINIMUM_DOWNTIME_DURATION
        self.maximum_timer_slack = DEFAULT_MAXIMUM_TIMER_SLACK

    def is_active(self):
        return True


class RecurringTask(object):

    def __init__(self, p_name, p_handler_method, p_interval=DEFAULT_TASK_INTERVAL, p_fixed_schedule=False):

        self.name = p_name
        self.handler_method = p_handler_method
        self.interval = p_interval
        self.next_execution = None
        self.fixed_schedule = p_fixed_schedule

    def __lt__(self, p_other):
        return self.next_execution < p_other

    def __gt__(self, p_other):
        return self.next_execution > p_other

    def __sub__(self, p_other):
        if isinstance(p_other, RecurringTask):
            return self.next_execution - p_other.next_execution

        else:
            return self.next_execution - p_other

    def __rsub__(self, p_other):
        if isinstance(p_other, RecurringTask):
            return p_other.next_execution - self.next_execution

        else:
            return p_other - self.next_execution

    def get_heap_entry(self):

        # return (self, self)
        return self

    def compute_next_execution_time(self):

        if self.next_execution is None:
            self.next_execution = datetime.datetime.utcnow()

        elif self.fixed_schedule:
            self.next_execution = self.next_execution + datetime.timedelta(seconds=self.interval)

        else:
            self.next_execution = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.interval)

    def adapt_to_delay(self, p_delay):

        if self.next_execution is not None:
            self.next_execution = self.next_execution + datetime.timedelta(seconds=p_delay)
            limit = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.interval)

            # Don't schedule more than one interval into the future!
            if self.next_execution > limit:
                self.next_execution = limit


class BaseApp(daemon.Daemon):

    def __init__(self, p_app_name, p_pid_file, p_arguments, p_dir_name, p_languages=None):

        super().__init__(pidfile=p_pid_file)

        self._app_name = p_app_name
        self._dir_name = p_dir_name
        self._languages = p_languages
        self._arguments = p_arguments
        self._logger = log_handling.get_logger(self.__class__.__name__)
        self._config = None
        self._recurring_tasks = []
        self._downtime = 0
        self._locale_helper = None
        self._latest_request = None
        self._partial_basic_init_executed = False
        self._full_basic_init_executed = False

        if self._languages is None:
            self._languages = DEFAULT_LANGUAGES

        self._langs = {}

        # Only temporary until the app has been initialized completely!
        self._app_config = BaseAppConfigModel()

    @property
    def locale_helper(self):

        return self._locale_helper

    def get_request_locale(self):
        locale = flask.request.accept_languages.best_match(self._languages)

        if self._latest_request is None or not self._latest_request is flask.request.stream:
            msg = "Best matching locale = {locale}"
            self._logger.debug(msg.format(locale=locale))
            self._latest_request = flask.request.stream
        return locale

    def add_locale_helper(self, p_locale_helper):

        if self._locale_helper is not None:
            p_locale_helper.chain_helper(self._locale_helper)

        self._locale_helper = p_locale_helper

    def init_babel(self, p_localeselector):

        babel_rel_directory = settings.extended_settings.get("babel_rel_directory")

        if babel_rel_directory is not None:

            locale_dir = os.path.join(os.path.dirname(__file__), babel_rel_directory)
            a_locale_helper = locale_helper.LocaleHelper(
                p_locale_dir=locale_dir, p_locale_selector=p_localeselector)

            self.add_locale_helper(a_locale_helper)

            fmt = "Module python_base_app is using Babel translations in {path}"
            self._logger.info(fmt.format(path=locale_dir))

        else:
            fmt = "Setting 'babel_rel_directory' not found "\
                  "-> no support for Babel translations for module 'python_base_app'"
            self._logger.warning(fmt)


    def gettext(self, p_text):

        return self._locale_helper.gettext(p_text)

    def get_user_configuration_filename(self):

        home = str(pathlib.Path.home())
        return os.path.join(home, DEFAULT_USER_CONFIG_DIR, self._app_name) + DEFAULT_CONF_EXTENSION


    def check_user_configuration_file(self, p_filename=None):

        if p_filename is None:
            p_filename = self.get_user_configuration_filename()

        fmt = "Looking for user configuration file in {path}"
        self._logger.info(fmt.format(path=p_filename))

        if os.path.exists(p_filename):
            self._arguments.configurations.append(p_filename)


    @property
    def down_time(self):
        return self._downtime

    def reset_down_time(self):
        self._downtime = 0

    def add_recurring_task(self, p_recurring_task):

        p_recurring_task.compute_next_execution_time()
        heapq.heappush(self._recurring_tasks, p_recurring_task.get_heap_entry())

    @staticmethod
    def configuration_factory():
        return configuration.Configuration()

    def prepare_configuration(self, p_configuration):

        self._app_config = p_configuration[self._app_name]

        for afile in self._arguments.configurations:
            p_configuration.read_config_file(afile)

        p_configuration.read_environment_parameters(p_environment_dict=os.environ)
        p_configuration.read_command_line_parameters(p_parameters=self._arguments.cmd_line_options)

        if self._app_config.log_level is not None:
            log_handling.set_level(self._app_config.log_level)

        if self._app_config.spool_dir is None:
            self._app_config.spool_dir = os.path.join(DEFAULT_SPOOL_BASE_DIR, self._dir_name)

        return p_configuration

    def load_configuration(self):

        self._config = self.prepare_configuration(self.configuration_factory())

    def write_config_to_file(self, p_filename=None):

        if p_filename is None:
            p_filename = self.get_user_configuration_filename()

        fmt = "Writing user configuration to file '{filename}'..."
        self._logger.info(fmt.format(filename=p_filename))

        self._config.write_to_file(p_filename=p_filename)

    def check_configuration(self):

        logger = log_handling.get_logger()

        self.prepare_configuration(self.configuration_factory())

        fmt = "%d configuration files are Ok!" % len(self._arguments.configurations)
        logger.info(fmt)

    def reevaluate_configuration(self):
        pass

    def handle_sighup(self, p_signum, p_stackframe):

        fmt = "Received signal %d" % p_signum
        _ = p_stackframe
        self._logger.info(fmt)

        raise exceptions.SignalHangUp()

    def install_handlers(self):

        signal.signal(signal.SIGTERM, self.handle_sighup)
        signal.signal(signal.SIGHUP, self.handle_sighup)
        signal.signal(signal.SIGINT, self.handle_sighup)  # CTRL-C
        signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGTERM, signal.SIGHUP, signal.SIGINT])

    def prepare_services(self, p_full_startup=True):

        pass

    #        if self._app_config.log_level is not None:
    #            log_handling.set_level(self._app_config.log_level)

    def start_services(self):

        pass

    def adapt_active_recurring_tasks(self, p_delay):

        # for (_next_execution, task) in self._recurring_tasks:
        #    task.adapt_to_delay(p_delay=p_delay)
        for task in self._recurring_tasks:
            task.adapt_to_delay(p_delay=p_delay)

        heapq.heapify(self._recurring_tasks)

    def stop_event_queue(self):
        self._done = True

    def event_queue(self):

        self._done = False

        while not self._done:
            try:
                now = datetime.datetime.utcnow()

                if len(self._recurring_tasks) > 0:
                    task = self._recurring_tasks[0]
                    wait_in_seconds = (task - now).total_seconds()

                else:
                    task = None
                    wait_in_seconds = ETERNITY

                if wait_in_seconds > 0:
                    try:
                        fmt = "Sleeping for {seconds} seconds (or until next signal)"
                        self._logger.debug(fmt.format(seconds=wait_in_seconds))

                        signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGTERM, signal.SIGHUP])
                        time.sleep(wait_in_seconds)

                    except exceptions.SignalHangUp as e:
                        raise e

                    except Exception as e:
                        if self._app_config.debug_mode:
                            fmt = "Propagating exception due to debug_mode=True"
                            self._logger.warn(fmt)
                            raise e

                        fmt = "Exception %s while waiting for signal" % str(e)
                        self._logger.error(fmt)

                    fmt = "Woken by signal"
                    self._logger.debug(fmt)

                    if task is not None:
                        now = datetime.datetime.utcnow()
                        overslept_in_seconds = (now - task).total_seconds()

                        if overslept_in_seconds > self._app_config.maximum_timer_slack:
                            self.track_downtime(p_downtime=overslept_in_seconds)

                if len(self._recurring_tasks) > 0:
                    task_executed = True

                    while task_executed:
                        task = self._recurring_tasks[0]
                        now = datetime.datetime.utcnow()

                        if now > task:
                            delay = (now - task).total_seconds()

                            task = heapq.heappop(self._recurring_tasks)
                            self.add_recurring_task(p_recurring_task=task)

                            fmt = "Executing task {task} {secs:.3f} [s] behind schedule... *** START ***"
                            self._logger.debug(fmt.format(task=task.name, secs=delay))
                            task.handler_method()
                            fmt = "Executing task {task} {secs:.3f} [s] behind schedule... *** END ***"
                            self._logger.debug(fmt.format(task=task.name, secs=delay))

                            if delay > self._app_config.minimum_downtime_duration:
                                self.track_downtime(p_downtime=delay)

                        else:
                            task_executed = False

                    if self._downtime > 0:
                        self.handle_downtime(p_downtime=int(self._downtime))
                        self.reset_down_time()

            except exceptions.SignalHangUp:
                fmt = "Event queue interrupted by signal"
                self._logger.info(fmt)

                self._done = True

            except Exception as e:
                if self._app_config.debug_mode:
                    fmt = "Propagating exception due to debug_mode=True"
                    self._logger.warn(fmt)
                    raise e

                fmt = "Exception %s in event queue" % str(e)
                self._logger.error(fmt)
                tools.log_stack_trace(p_logger=self._logger)

            if self._arguments.single_run:
                self._done = True

    def track_downtime(self, p_downtime):

        fmt = "Detected delay of {seconds} seconds -> adding to downtime timer"
        self._logger.info(fmt.format(seconds=p_downtime))

        self._downtime += p_downtime
        self.adapt_active_recurring_tasks(p_delay=p_downtime)

    def handle_downtime(self, p_downtime):

        fmt = "Accumulated downtime of {seconds} seconds ignored."
        self._logger.warning(fmt.format(seconds=p_downtime))

    def stop_services(self):

        pass

    def basic_init(self, p_full_startup=True):

        if self._full_basic_init_executed:
            return

        if self._partial_basic_init_executed and not p_full_startup:
            return

        self._full_basic_init_executed = p_full_startup
        self._partial_basic_init_executed = True

        try:
            self.prepare_services(p_full_startup=p_full_startup)

        except Exception as e:
            fmt = "Error '{msg}' in basic_init()"
            self._logger.error(fmt.format(msg=str(e)))
            raise e

    def run(self):

        previous_exception = None

        if tools.running_in_docker():
            self._logger.info("Detected Docker run time.")

        elif tools.running_in_snap():
            self._logger.info("Detected Snapcraft run time")

        fmt = "Starting app '%s'" % self._app_name
        self._logger.info(fmt)


        try:
            self.basic_init()
            self.install_handlers()
            self.start_services()
            self.event_queue()

        except Exception as e:
            fmt = "Exception '%s' in run()" % str(e)
            self._logger.error(fmt)

            previous_exception = e

        finally:
            try:
                self.stop_services()

            except Exception as e:
                fmt = "Exception '%s' while stopping services" % str(e)
                self._logger.error(fmt)

        if previous_exception is not None:
            raise previous_exception

        fmt = "Terminating app '%s'" % self._app_name
        self._logger.info(fmt)

    def run_special_commands(self, p_arguments):

        _arguments = p_arguments
        return False


def get_argument_parser(p_app_name):
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', nargs='*', dest='configurations', default=[],
                        help='file names of the configuration files')
    parser.add_argument('--option', nargs='*', dest='cmd_line_options', default=[],
                        help='Additional configuration settings formatted as '
                             'SECTION.OPTION=VALUE (overriding settings in configuration files)')
    parser.add_argument('--pidfile', dest='pid_file',
                        help='name of the PID file', default='/var/run/%s/%s.pid' % (p_app_name, p_app_name))
    parser.add_argument('--logdir', dest='log_dir', default=None,
                        help='base path for logging files')
    parser.add_argument('--loglevel', dest='log_level', default=DEFAULT_LOG_LEVEL,
                        help='logging level', choices=['WARN', 'INFO', 'DEBUG'])
    parser.add_argument('--no-log-filter', dest='no_log_filter', default=DEFAULT_NO_LOG_FILTER,
                        action='store_const', const=True,
                        help='deactivate log filter showing thread and user information')
    parser.add_argument('--application-owner', dest='app_owner', default=None,
                        help='name of user running application')
    parser.add_argument('--daemonize', dest='daemonize', action='store_const', const=True, default=False,
                        help='start app as daemon process')
    parser.add_argument('--check-installation', dest='check_installation', action='store_const', const=True,
                        default=False,
                        help='Tests the existence of required directories and files as well as their access rights')
    parser.add_argument('--check-configuration', dest='check_configuration', action='store_const', const=True,
                        default=False,
                        help='Validates the configurations files')
    parser.add_argument('--kill', dest='kill', action='store_const', const=True, default=False,
                        help='Terminates the running daemon process')
    parser.add_argument('--single-run', dest='single_run', action='store_const', const=True, default=False,
                        help='Executes a single run of the application and exists')

    return parser


def check_installation(p_arguments):
    pid_file_directory = os.path.dirname(p_arguments.pid_file)

    if p_arguments.log_dir is not None:
        tools.test_mode(p_arguments.log_dir, p_app_owner=p_arguments.app_owner, p_is_directory=True, p_executable=True,
                        p_writable=True, p_other_access=False)

    if p_arguments.daemonize:
        tools.test_mode(pid_file_directory, p_app_owner=p_arguments.app_owner, p_is_directory=True, p_executable=True,
                        p_writable=True)

    for config_file in p_arguments.configurations:
        tools.test_mode(config_file, p_app_owner=p_arguments.app_owner, p_other_access=False)

    logger = log_handling.get_logger()
    logger.info("Installation OK!")


def main(p_app_name, p_app_class, p_argument_parser):
    process_result = 0
    logger = log_handling.get_logger()
    arguments = p_argument_parser.parse_args()

    try:
        if arguments.daemonize and arguments.log_dir is None:
            raise configuration.ConfigurationException("Option --daemonize requires option --logdir!")

        default_log_file = '%s.log' % p_app_name

        log_handling.start_logging(p_level=arguments.log_level, p_log_dir=arguments.log_dir,
                                   p_log_file=default_log_file, p_use_filter=not arguments.no_log_filter)
        logger = log_handling.get_logger()

        for path in CONTRIB_LOG_PATHS:
            msg = "Setting log filter for library {path}..."
            logger.debug(msg.format(path=path))

            log_handling.add_default_filter_to_logger_by_name(path)

        if arguments.check_installation:
            logger.info("Checking installation...")
            check_installation(p_arguments=arguments)

        else:
            app = p_app_class(p_pid_file=arguments.pid_file, p_arguments=arguments, p_app_name=p_app_name)

            if len(arguments.configurations) == 0:
                logger.warning("No configuration files specified")

            if arguments.kill:
                logger.info("Killing active daemon process...")
                app.stop()

            elif arguments.check_configuration:
                logger.info("Checking configuration files...")
                app.check_configuration()

            else:
                app.load_configuration()

                if not app.run_special_commands(p_arguments=arguments):
                    if arguments.daemonize:
                        logger.info("Starting daemon process...")
                        app.start()

                    else:
                        logger.info("Starting as a normal foreground process...")
                        app.run()

    except configuration.ConfigurationException as e:
        logger.error(str(e))
        process_result = 3

    except exceptions.InstallationException as e:
        logger.error(str(e))
        process_result = 2

    except Exception as e:
        tools.handle_fatal_exception(p_exception=e, p_logger=logger)
        tools.log_stack_trace(p_logger=logger)
        process_result = 1

    fmt = 'Terminated with exit code %d' % process_result
    logger.info(fmt)

    return process_result
