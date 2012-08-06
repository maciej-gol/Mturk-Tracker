import time
import logging
from utils.pid import Pid

from django.core.management.base import BaseCommand, NoArgsCommand
from optparse import make_option
from mturk.toprequesters.reports import ToprequestersReport

HOURS4 = 60 * 60 * 4

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command for populating toprequesters reports into cache.

    Allows the user to see available reports and their status, cache all or
    selected reports.

    """

    option_list = NoArgsCommand.option_list + (
        make_option('--days', dest='days', default='30',
            help='Number of days from which the history data is grabbed.'),
        make_option('--force', dest='force', action="store_true", default=False,
            help='Enforces overriding existing entry in the cache.'),
        make_option('--all', dest='all', action="store_true", default=False,
            help='Evaluates all reports available.'),
        make_option('--list', dest='list', action="store_true", default=False,
            help='Shows a list of available report types.'),
        make_option('--purge', dest='purge', action="store_true", default=False,
            help='Removes all or the selected report from cache.'),
        make_option('--report-type', dest='report-type', type="int",
            default=None, help='The report to rebuild.'),
    )
    help = 'Make sure top requesters are in cache.'

    def handle(self, **options):
        """Main command entry point."""

        self.options = options

        if self.options['list']:
            pass  # do nothing, go straight to print_status
        else:
            pid = Pid('mturk_cache_topreq', True)
            self.prepare_options()  # sets self.reports and prints errors is any
            self.reports and (self.handle_purge() or self.handle_cache())
            pid.remove_pid()

        self.print_status()

    def prepare_options(self):
        """Sets self.reports with an array of data to process or None.
        Prints any errors occuring.

        """
        self.reports = None
        if self.options.get('all'):
            self.reports = ToprequestersReport.values
        else:
            report_type = self.options.get('report-type')
            if report_type in ToprequestersReport.values:
                self.reports = [report_type]
            else:
                if report_type is None:
                    log.info('Please specify "--report-type=<type>" or '
                        '"--all".')
                else:
                    log.info('Unknown report type: "{0}".'.format(
                        report_type))

    def handle_cache(self):
        """Handles the primary cache function of this command."""
        log.info('Caching reports: {0}.'.format(self.reports))
        for report_type in self.reports:
            self.__cache_report(report_type)

    def __cache_report(self, report_type):
        """Evaluates the report and stores it under correct cache key."""

        display_name = ToprequestersReport.display_names[report_type]

        if ToprequestersReport.is_cached(report_type):
            if self.options['force']:
                log.info('Recalculating "{0}" toprequesters report.'.format(
                    display_name))
            else:
                log.info('"{0}" toprequesters still in cache, use --force flag'
                    ' to rebuild anyway.'.format(display_name))
                return False
        else:
            log.info(('"{0}" toprequesters report missing, recalculating.'
                ).format(display_name))

        start_time = time.time()

        days = self.options['days']
        data = ToprequestersReport.REPORT_FUNCTION[report_type](days)
        log.info('Toprequesters report "{0}" generated in: {1}s.'.format(
            display_name, time.time() - start_time))

        # too often we get no information on the success of caching
        if not data:
            log.warning('Data returned by report function is {0}!'.format(data))
        else:
            ToprequestersReport.store(report_type, data)
            if not ToprequestersReport.is_cached(report_type):
                log.warning('Cache error - data could not be fetched!')
        return True

    def handle_purge(self):
        """Handles purge option. Removes all data if --all was used or spefified
        --report-type."""
        if self.options['purge']:
            log.info("Removing data for {0}.".format(self.reports))
            for r in self.reports:
                ToprequestersReport.purge(r)
            self.print_status()
        return self.options['purge']

    def print_status(self):
        """Shows report availability report."""
        log.info("Available report types: \n" +
                ToprequestersReport.get_available_as_str())
