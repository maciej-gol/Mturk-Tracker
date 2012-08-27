# -*- coding: utf-8 -*-

import time
import datetime
import logging
import dateutil.parser

from optparse import make_option
from django.utils.timezone import now
from django.core.management.base import BaseCommand

from mturk.main.models import Crawl

log = logging.getLogger(__name__)


class DataUpdaterCommand(BaseCommand):

    log = log

    help = ("Base for data traversing commands.")
    display_name = None

    option_list = BaseCommand.option_list + (
        make_option('--start', dest="start", default=None,
            help='Processed interval start, defaults to 2 hours.'),
        make_option('--end', dest="end", default=None,
            help='Processed interval end, defaults to now.'),
        make_option('--minutes', dest="minutes", default=None, type='int',
            help='Minutes to look back for records.'),
        make_option('--hours', dest="hours", default=None, type='int',
            help='Hours to look back for records.'),
        make_option('--chunk-size', dest="chunk-size", default=10, type='int',
            help='How many models should be processed in a batch.'),
    )

    min_crawls = 1
    overlap = 0
    chunk_size = 1

    def process_args(self, options):
        """Sets the following options on this instance:

        * chunk_size
        * start
        * end

        """
        if isinstance(options.get('start'), basestring):
            options['start'] = dateutil.parser.parse(options.get('start'))
        if isinstance(options.get('end'), basestring):
            options['end'] = dateutil.parser.parse(options.get('end'))

        self.chunk_size = options.get('chunk-size')

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

        self.start = start
        self.end = end
        self.options = options

        return options

    @staticmethod
    def chunks(self, items, chunk, overlap):
        """ Yield successive chunks of ``chunk`` items overlapping by
        ``overlap`` items.
        """
        assert chunk > overlap, "Chunk size must be greater than overlap!"
        for i in xrange(0, len(items), chunk - overlap):
            yield items[i:i + chunk]

    def get_elapsed(self):
        return time.time() - self.start_time

    def short_date(self):
        return now().time().strftime('%H:%M:%S')

    def filter_crawls(self, crawls):
        """Override to add any extra filter required on crawls."""
        return crawls

    def order_crawls(self, crawls):
        """Orders the crawls by start_time, override to change the default."""
        return crawls.order_by('-start_time')

    def get_crawls(self):
        """Returns crawls to process."""
        return self.order_crawls(self.filter_crawls(Crawl.objects.filter(
            start_time__gt=self.start, start_time__lt=self.end)))

    def prepare_data(self):
        """Override to add any data check/preparation required. This method is
        called once after querying the data and before entering the main
        updater loop."""
        pass

    def process_chunk(self, start, end, chunk):
        """Override to add the core data processing method."""
        pass

    def handle(self, **options):

        self.start_time = time.time()
        self.process_args(options)

        try:
            # query crawls in the period we want to process
            crawls = self.get_crawls()
            total_count = len(crawls)

            if total_count < self.min_crawls:
                self.log.info("Not enough crawls to process.")
                return

            self.prepare_data()

            done = 0
            self.log.info("""
            Starting {6} update.

            {0} crawls will be processed in chunks of {3} (overlap: {7}).
            -- {1} to
            -- {2},
            id from {4} to {5}.
            """.format(total_count,
                self.start.strftime('%y-%m-%d %H:%M:%S'),
                self.end.strftime('%y-%m-%d %H:%M:%S'),
                self.chunk_size,
                crawls[0].id, crawls[total_count - 1].id,
                self.display_name, self.overlap))

            # iterate over overlapping chunks of crawls list
            for chunk in self.chunks(crawls, self.chunk_size,
                    overlap=self.overlap):
                start, end = (chunk[-1].start_time, chunk[0].start_time)
                self.log.info(('Chunk of {0} crawls: {1}\nstart_time {2} to '
                    '{3}.').format(len(chunk), [c.id for c in chunk],
                    start.strftime('%y-%m-%d %H:%M:%S'),
                    end.strftime('%y-%m-%d %H:%M:%S')))
                chunk_time = time.time()

                if not self.process_chunk(start, end, chunk):
                    break

                done += len(chunk) - self.overlap
                self.log.info(('Chunk processed in {0}s, total {1}s, {2}/{3}'
                    ' done.').format(time.time() - chunk_time,
                    self.get_elapsed(), done, total_count - 1))

        except Exception as e:
            self.log.exception(e)
        else:
            self.log.info('{0} crawls processed in {1}s, exiting.'.format(
                total_count, self.get_elapsed()))
