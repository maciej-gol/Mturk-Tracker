# -*- coding: utf-8 -*-
import time
import datetime
import logging

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
            help='Processed interval start, defaults to now - 4 hours.'),
        make_option('--end', dest="end", default=None,
            help='Processed interval end, defaults to now.'),
        make_option('--minutes', dest="minutes", default=None, type='int',
            help='Minutes to look back for records.'),
        make_option('--hours', dest="hours", default=None, type='int',
            help='Hours to look back for records.'),
        )

    def handle(self, **options):

        pid = Pid(self.proc_name, True)

        start_time = time.time()

        try:

            if options.get('minutes') or options.get('hours'):
                timedelta = datetime.timedelta(
                    minutes=options.get('minutes', 0),
                    hours=options.get('hours', 0))
            else:
                timedelta = datetime.timedelta(hours=2)

            if options['end'] and options['start'] is None:
                start = options['end'] - timedelta
                end = options['end']
            else:
                start = options['start'] or (now() - timedelta)
                end = options['end'] or now()

            cur = connection.cursor()

            self.logger.info('Calling {0}({1}, {2}), start time: {3}.'.format(
                self.proc_name, start, end, now()))

            cur.callproc(self.proc_name, [start, end])

            cur.execute('commit;')

            self.logger.info('{0} for crawls from {1} to {2} took: {3}'.format(
                self.proc_name, start, end, time.time() - start_time))

        except Exception as e:
            log.exception(e)

        pid.remove_pid()
