# -*- coding: utf-8 -*-

import time
import logging

from optparse import make_option
from django.db.models import F
from django.core.management import call_command
from django.conf import settings

from utils.management.commands.base.crawl_updater import CrawlUpdaterCommand
from utils.sql import execute_sql


class Command(CrawlUpdaterCommand):

    help = ("Wraps all 3 commands that need to be ran in order to "
        "calculate data for day stats.")

    log = logging.getLogger('mturk.arrivals')

    option_list = CrawlUpdaterCommand.option_list + (
        make_option("--clear-existing", dest="clear-existing", default=False,
            action="store_true",
            help='If true, related hits_posted and hits_consumed will be set '
            'to 0 before proceeding.'),
    )

    min_crawls = 2
    overlap = 1
    chunk_size = 10
    display_name = 'arrivals'

    # django management commands to run per each chunk in the given order
    COMMANDS = (
        'db_hits_temp_population',
        'db_hits_update',
        'db_initial_post_hits_update',
        'db_reward_population'
    )

    def prepare_data(self):
        self.options['clear-existing'] and self.clear_past_results()
        execute_sql('truncate hits_temp', commit=True).close()

    def filter_crawls(self, crawls):
        return crawls.filter(groups_downloaded__gt=F('groups_available') *
            settings.INCOMPLETE_CRAWL_THRESHOLD)

    def process_chunk(self, start, end, chunk):
        for c in self.COMMANDS:
            self.log.info('Calling {0}, {1}.'.format(c, self.short_date()))
            ctime = time.time()
            call_command(c, start=start, end=end, pidfile='arrivals',
                verbosity=0, logger='mturk.arrivals')
            self.log.info('{0}s elapsed.'.format(time.time() - ctime))
        return True

    def clear_past_results(self):
        """Clears results in hits_mv and main_crawlagregates tables.

        Tables cleared:
        hits_mv -- hits_posted and hits_consumed
        main_crawlagregates -- hits_consumed, hits_posted, hitgroups_posted,
        hitgroups_consumed

        """
        self.log.info('Clearing existiting hits_mv columns.')
        clear_time = time.time()
        execute_sql(
        """UPDATE hits_mv SET hits_posted = 0, hits_consumed = 0
        WHERE
            crawl_id IN (
                SELECT id FROM main_crawl
                WHERE start_time BETWEEN '{0}' AND '{1}'
            ) AND
            hits_posted > 0 OR hits_consumed > 0;
        """.format(self.start.isoformat(), self.end.isoformat()),
        commit=True).close()
        self.log.info('{0}s elapsed.'.format(time.time() - clear_time))

        self.log.info('Clearing existiting main_crawlagregates columns.')
        clear_time = time.time()
        execute_sql(
        """UPDATE main_crawlagregates
        SET
            hits_posted = 0, hits_consumed = 0,
            hitgroups_posted = 0, hitgroups_consumed = 0
        WHERE
            crawl_id IN (
                SELECT id FROM main_crawl
                WHERE start_time BETWEEN '{0}' AND '{1}'
            ) AND (
            hits_posted > 0 OR hits_consumed > 0 OR
            hitgroups_consumed > 0 OR hitgroups_posted > 0);
        """.format(self.start.isoformat(), self.end.isoformat()),
        commit=True).close()
        self.log.info('{0}s elapsed.'.format(time.time() - clear_time))
