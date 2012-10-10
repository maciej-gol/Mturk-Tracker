# -*- coding: utf-8 -*-
import time
import logging

from optparse import make_option
from django.db import connection, transaction
from django.utils.timezone import now

from utils.management.commands.base.time_args_command import TimeArgsCommand
from utils.pid import Pid

log = logging.getLogger(__name__)


class DBProcedureCommand(TimeArgsCommand):

    help = 'Django management command for running a stored function.'
    proc_name = ''
    """Name of the procedure in the database."""
    logger = log
    """Logger instance to use. Altered by command line paremeters."""

    option_list = TimeArgsCommand.option_list + (
        make_option('--pidfile', dest="pidfile", default=None,
            help='The pidfile to use.'),
        make_option('--logger', dest="logger", default=None,
            help='The logger instance to use.'),
        )

    def process_options(self, options):
        """Calls parent process_options to populate time relater fields."""
        self.options = super(DBProcedureCommand, self).process_options(options)
        self.pidfile = (self.options.get('pidfile') or
                        getattr(self, 'pidfile', None) or
                        self.proc_name)
        self.logger = logging.getLogger(self.options.get('logger') or __name__)
        if self.options.get('verbosity') == 0:
            self.logger.setLevel(logging.WARNING)
        return self.options

    def get_proc_args(self):
        """Returns arguments for the database function call."""
        return [self.start, self.end]

    def handle(self, **options):

        self.process_options(options)

        pid = Pid(self.pidfile, True)
        start_time = time.time()

        try:

            cur = connection.cursor()

            self.logger.info('Calling {0}({1}, {2}), start time: {3}.'.format(
                self.proc_name, self.start, self.end, now()))

            cur.callproc(self.proc_name, self.get_proc_args())

            transaction.commit_unless_managed()

            self.logger.info('{0} for crawls from {1} to {2} took: {3}.'.format(
                self.proc_name, self.start, self.end, time.time() - start_time))

        except Exception as e:
            self.logger.exception(e)
        finally:
            pid.remove_pid()
            if options.get('verbosity') == 0:
                self.logger.setLevel(logging.DEBUG)
