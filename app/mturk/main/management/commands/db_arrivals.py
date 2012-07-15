# -*- coding: utf-8 -*-

import time
import datetime
import logging
import dateutil.parser

from optparse import make_option
from django.utils.timezone import now
from django.core.management.base import BaseCommand
from django.core.management import call_command

from mturk.main.models import Crawl

log = logging.getLogger('mturk.arrivals.db_arrivals')


class Command(BaseCommand):

    help = ("Wraps all 3 commands that need to be ran in order to "
        "calculate data for day stats.")

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
            help='How many crawls should be processed in a batch.'),
        )

    def process_args(self, options):

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

        return start, end

    # django management commands to run per each chunk in the given order
    COMMANDS = (
        'db_hits_temp_population',
        'db_hits_update',
        'db_reward_population'
    )

    def chunks(self, items, chunk, overlap):
        """ Yield successive chunks of ``chunk`` items overlapping by
        ``overlap`` items.
        """
        chunk -= overlap
        for i in xrange(1, len(items), chunk):
            yield items[i - 1:i + chunk]

    def get_elapsed(self):
        return time.time() - self.start_time

    def short_date(self):
        return now().time().strftime('%H:%M:%S')

    def handle(self, **options):

        self.start_time = time.time()
        self.process_args(options)

        try:

            # query crawls in the period we want to process
            crawls = Crawl.objects.filter(start_time__gt=self.start,
                start_time__lt=self.end).order_by('-start_time')
            total_count = len(crawls)
            done = 1
            log.info("""
            Starting arrivals calculation.

            {0} crawls will be processed in chunks of {3}.
            -- {1} to
            -- {2},
            -- id from {4} to {5}.
            """.format(total_count,
                self.start.strftime('%y-%m-%d %H:%M:%S'),
                self.end.strftime('%y-%m-%d %H:%M:%S'),
                self.chunk_size,
                crawls[0].id, crawls[total_count - 1].id))

            # iterate over overlapping chunks of crawls list
            for chunk in self.chunks(crawls, self.chunk_size, overlap=1):
                start, end = (chunk[-1].start_time, chunk[0].start_time)
                log.info(('Chunk of {0} crawls: {1}\nstart_time {2} to '
                    '{3}.').format(len(chunk), [c.id for c in chunk],
                    start.strftime('%y-%m-%d %H:%M:%S'),
                    end.strftime('%y-%m-%d %H:%M:%S')))

                # run commands responsible for populating data
                # it's important that they query the crawls in a similar way
                # so that the data is processed correctly
                for c in self.COMMANDS:
                    log.info('Calling {0}, {1}.'.format(c, self.short_date()))
                    ctime = time.time()
                    call_command(c, start=start, end=end, pidfile='arrivals',
                        verbosity=0)
                    log.info('{0}s elapsed.'.format(time.time() - ctime))

                done += len(chunk) - 1
                log.info('Chunk processed in {0}s, {1}/{2} done.'.format(
                    self.get_elapsed(), done, total_count))

        except Exception as e:
            log.exception(e)
        else:
            log.info('{0} crawls processed in {1}s, exiting.'.format(
                total_count, self.get_elapsed()))
