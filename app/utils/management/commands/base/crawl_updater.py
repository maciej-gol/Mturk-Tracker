# -*- coding: utf-8 -*-

import math
import time
import logging

from optparse import make_option
from django.utils.timezone import now

from utils.management.commands.base.time_args_command import TimeArgsCommand
from utils.pid import Pid

from mturk.main.models import Crawl

log = logging.getLogger('mturk.aggregates')


class CrawlUpdaterCommand(TimeArgsCommand):

    log = log
    """If required override self.log in inheriting commands."""

    help = ("Base for data traversing commands.")

    option_list = TimeArgsCommand.option_list + (
        make_option('--chunk-size', dest="chunk-size", default=10, type='int',
            help='How many models should be processed in a batch.'),
    )

    display_name = None
    """Name used to identify this command in log messages."""
    pid_file = None
    """Name of the pid file to use (without the extension)."""
    min_crawls = 1
    """Minimal number of crawls required to run this command."""
    chunk_size = 1
    """Size of each chunk."""
    overlap = 0
    """Number of records that should overlap between chunks."""

    def process_options(self, options):
        """Calls TimeArgsCommand.process_options to have time options populated.

        Additionally sets the following options on this instance:
        * chunk_size

        """
        self.options = super(CrawlUpdaterCommand, self).process_options(options)
        self.chunk_size = self.options.get('chunk-size')
        return self.options

    def chunks(self, items, chunk, overlap):
        """ Yield successive chunks of ``chunk`` items overlapping by
        ``overlap`` items.
        """
        assert chunk > overlap, "Chunk size must be greater than overlap!"
        for i in xrange(0, len(items), chunk - overlap):
            yield items[i:i + chunk]

    chunk_times = []

    def store_chunk_time(self, elapsed):
        self.chunk_times.append(elapsed)

    def get_eta(self, last=10):
        """Returns estimated remaining time based on ``last`` chunks' times."""
        last = last if len(self.chunk_times) >= last else len(self.chunk_times)
        return ((math.ceil(self.total_count / self.chunk_size)
            - len(self.chunk_times)) *
            sum(self.chunk_times[-last:]) / last)

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
        called once before querying any data."""
        pass

    def process_chunk(self, start, end, chunk):
        """Override to add the core data processing method.

        To abort the procedure after the given chunk, return value evaluting to
        False from the function. To continue receiving chunks, return True.
        """
        pass

    def handle(self, **options):

        pid = Pid(self.pid_file) if self.pid_file else None

        self.start_time = time.time()
        self.process_options(options)

        try:

            self.prepare_data()

            # query crawls in the period we want to process
            crawls = self.get_crawls()
            self.total_count = len(crawls)
            if self.total_count < self.min_crawls:
                self.log.info("Not enough crawls to process.")
                return

            done = 0
            self.log.info("""
            Starting {6}.

            {0} crawls will be processed in chunks of {3} (overlap: {7}).
            -- {1} to
            -- {2},
            id from {4} to {5}.
            """.format(self.total_count,
                self.start.strftime('%y-%m-%d %H:%M:%S'),
                self.end.strftime('%y-%m-%d %H:%M:%S'),
                self.chunk_size,
                crawls[0].id, crawls[self.total_count - 1].id,
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

                chunk_time = time.time() - chunk_time
                self.store_chunk_time(chunk_time)
                done += len(chunk) - self.overlap
                self.log.info(('Chunk processed in {0}s, total {1}s, {2}/{3}'
                    ' done, ETA: {4} minutes.').format(chunk_time,
                    self.get_elapsed(), done, self.total_count - self.overlap,
                    self.get_eta() / 60))

        except Exception as e:
            self.log.exception(e)
        else:
            self.log.info('{0} crawls processed in {1}s, exiting.'.format(
                self.total_count, self.get_elapsed()))
        finally:
            pid and pid.remove_pid()
