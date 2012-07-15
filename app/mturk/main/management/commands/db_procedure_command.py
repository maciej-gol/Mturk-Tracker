# -*- coding: utf-8 -*-
import time
import datetime
import logging

import dateutil.parser
from optparse import make_option
from django.db import connection
from django.utils.timezone import now
from django.core.management.base import BaseCommand
from utils.pid import Pid

log = logging.getLogger(__name__)


class DBProcedureCommand(BaseCommand):
    help = ''
    proc_name = ''
    logger = log

    option_list = BaseCommand.option_list + (
        make_option('--start', dest="start", default=None,
            help='Processed interval start, defaults to 2 hours.'),
        make_option('--end', dest="end", default=None,
            help='Processed interval end, defaults to now.'),
        make_option('--minutes', dest="minutes", default=None, type='int',
            help='Minutes to look back for records.'),
        make_option('--hours', dest="hours", default=None, type='int',
            help='Hours to look back for records.'),
        make_option('--pidfile', dest="pidfile", default=None,
            help='The pidfile to use.'),
        )

    def process_args(self, options):

        if isinstance(options.get('start'), basestring):
            options['start'] = dateutil.parser.parse(options.get('start'))
        if isinstance(options.get('end'), basestring):
            options['end'] = dateutil.parser.parse(options.get('end'))

        if (options.get('minutes') is not None or
            options.get('hours') is not None):

            timedelta = datetime.timedelta(
                minutes=options.get('minutes') or 0,
                hours=options.get('hours') or 0)
        else:
            timedelta = datetime.timedelta(hours=2)

        if options['end'] and options['start'] is None:
            start = options['end'] - timedelta
            end = options['end']
        else:
            start = options['start'] or (now() - timedelta)
            end = options['end'] or now()

        self.pidfile = (options.get('pidfile') or
                        getattr(self, 'pidfile', None) or
                        self.proc_name)
        self.start = start
        self.end = end

        if options.get('verbosity') == 0:
            self.logger.setLevel(logging.WARNING)

        return start, end

    def handle(self, **options):

        self.process_args(options)

        pid = Pid(self.pidfile, True)
        start_time = time.time()

        try:

            cur = connection.cursor()

            self.logger.info('Calling {0}({1}, {2}), start time: {3}.'.format(
                self.proc_name, self.start, self.end, now()))

            cur.callproc(self.proc_name, [self.start, self.end])

            cur.execute('commit;')

            self.logger.info('{0} for crawls from {1} to {2} took: {3}'.format(
                self.proc_name, self.start, self.end, time.time() - start_time))

        except Exception as e:
            log.exception(e)
        finally:
            pid.remove_pid()
