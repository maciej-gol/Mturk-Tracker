# -*- coding: utf-8 -*-
import time
import datetime
import logging

from optparse import make_option
from django.utils.timezone import now
from django.core.management.base import BaseCommand

from utils.sql import execute_sql
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
        )

    def handle(self, **options):

        pid = Pid(self.proc_name, True)
        start_time = time.time()

        self.logger.info('Starting {0}.'.format(self.proc_name))

        start = options['start'] or (now() - datetime.timedelta(hours=4))
        end = options['end'] or now()

        execute_sql("select * from {0}('{1}', '{2}')".format(
            self.proc_name, start, end))

        self.logger.info('{0} took: {1}'.format(
            self.proc_name, time.time() - start_time))

        pid.remove_pid()
