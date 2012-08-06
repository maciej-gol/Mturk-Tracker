import time
import logging
from django.core.cache import cache
from utils.pid import Pid

from django.core.management.base import BaseCommand, NoArgsCommand
from optparse import make_option
from mturk.toprequesters.reports import ToprequestersReport

HOURS4 = 60 * 60 * 4

log = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--days', dest='days', default='30',
            help='Number of days from which the history data is grabbed.'),
        make_option('--force', dest='force', action="store_true", default=False,
            help='Enforces overriding existing entry in the cache.'),
        make_option('--report-type', dest='report-type', type="int",
            default=ToprequestersReport.AVAILABLE,
            help='The report to rebuild.'),
    )
    help = 'Make sure top requesters are in cache.'

    def handle(self, **options):

        pid = Pid('mturk_cache_topreq', True)

        report_type = options.get('report-type')
        if report_type not in ToprequestersReport.values:
            log.info('Unknown report type: "{0}".'.format(report_type))
            return

        key = ToprequestersReport.get_cache_key(report_type)
        display_name = ToprequestersReport.display_names[report_type]

        if cache.get(key) is None:
            log.info(('"{0}" toprequesters report missing, recalculating.'
                ).format(display_name))
        else:
            if options['force']:
                log.info('Recalculating "{0}" toprequesters report.'.format(
                    display_name))
            else:
                log.info('"{0}" toprequesters still in cache, use --force flag'
                    ' to rebuild anyway.'.format(display_name))
                return

        days = options['days']
        # no chache perform query:
        start_time = time.time()
        data = ToprequestersReport.REPORT_FUNCTION[report_type](days)
        log.info('Toprequesters report "{0}" generated in: {1}s.'.format(
            display_name, time.time() - start_time))

        # too often we get no information on the success of caching
        if not data:
            log.warning('Data returned by report function is {0}!'.format(data))
        else:
            cache.set(key, data, HOURS4)
            in_cache = cache.get(key, data)
            if in_cache is None:
                log.warning('Cache error - data could not be fetched!')

        pid.remove_pid()
