# -*- coding: utf-8 -*-

import sys
import datetime
import pytz
import dateutil.parser

from optparse import make_option
from django.utils.timezone import now, make_aware, is_naive
from django.core.management.base import BaseCommand


class TimeArgsCommand(BaseCommand):

    help = ("Base command for commands requiring start and end date arguments.")

    use_date_defaults = True
    """When false, at least start or end option will be required."""

    option_list = BaseCommand.option_list + (
        make_option('--start', dest="start", default=None,
            help='Processed interval start, defaults to 2 hours.'),
        make_option('--end', dest="end", default=None,
            help='Processed interval end, defaults to now.'),
        make_option('--minutes', dest="minutes", default=None, type='int',
            help='Minutes to look back for records.'),
        make_option('--hours', dest="hours", default=None, type='int',
            help='Hours to look back for records.'),
        make_option('--days', dest="days", default=None, type='int',
            help='Days to look back for records.'),
    )

    def process_options(self, options):
        """Sets the following options on this instance:

        * start -- start of the interval
        * end -- end of the interval
        * timedelta -- timedelta that was specified using minutes, hours and
        days
        * options -- options provided to the method

        Note: If the timezone info is empty, dates are assumed to be in UTC.
        """
        if not options['end'] and not options['start']:
            if not self.use_date_defaults:
                self.log.error('You must specify at least start or end '
                    'argument.')
                sys.exit(0)

        def subdict(keys, d):
            return dict(zip([a for a in keys if a in d], map(d.get, keys)))

        if isinstance(options.get('start'), basestring):
            options['start'] = dateutil.parser.parse(options.get('start'))
        if isinstance(options.get('end'), basestring):
            options['end'] = dateutil.parser.parse(options.get('end'))

        if (options.get('minutes') or options.get('hours') or
            options.get('days')):
            t = datetime.timedelta(
                **subdict(['minutes', 'hours', 'days'], options))
        else:
            t = datetime.timedelta(hours=2)

        if options['end'] and options['start'] is None:
            start = options['end'] - t
            end = options['end']
        else:
            start = options['start'] or (now() - t)
            end = options['end'] or now()

        def assure_aware(d):
            return make_aware(d, pytz.utc) if is_naive(d) else d

        options['start'] = start = assure_aware(start)
        options['end'] = end = assure_aware(end)

        self.timedelta = t
        self.options = options
        self.start = start
        self.end = end

        return options
