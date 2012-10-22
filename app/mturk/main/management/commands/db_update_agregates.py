# -*- coding: utf-8 -*-
import sys
import time
import logging
from optparse import make_option
from django.db import transaction
from django.conf import settings

from utils.pid import Pid
from utils.sql import execute_sql, query_to_dicts
from utils.management.commands.base.time_args_command import TimeArgsCommand
from mturk.main.management.commands.crawler_common import grab_error

log = logging.getLogger('mturk.aggregates')


class Command(TimeArgsCommand):

    help = 'Refreshes crawl aggregates.'

    option_list = TimeArgsCommand.option_list + (
        make_option("--clear-existing", dest="clear-existing",
            default=False, action="store_true",
            help='If true, related main_crawlagregates record will be deleted '
                'prior to update.'),
    )

    def process_options(self, options):
        super(Command, self).process_options(options)
        self.clear_existing = self.options['clear-existing']

    def handle(self, **options):

        pid = Pid('mturk_aggregates', True)

        self.process_options(options)
        start_time = time.time()

        log.info('Updating crawl agregates')
        update_crawl_agregates(start=self.start, end=self.end,
            clear_existing=self.clear_existing)
        log.info('db_update_agregates took: %s' % (time.time() - start_time))

        pid.remove_pid()


def update_crawl_agregates(commit_threshold=1000,
        start=None, end=None, clear_existing=False):
    """Creates main_crawlagregates records for hits_mv."""

    def print_status(number, row_id):
        log.info('Commited after %s crawls, last id %s.' % (number, row_id))

    clear_existing and start and end and clear_existing_rows(start, end)

    i = 0
    for i, row in enumerate(get_crawls(start=start, end=end)):
        try:
            execute_sql("""
            INSERT INTO
                main_crawlagregates (hits, start_time, reward, crawl_id, id,
                    projects, spam_projects)
            SELECT
                sum(hits_available) as "hits",
                start_time,
                sum(reward * hits_available) as "reward",
                crawl_id,
                nextval('main_crawlagregates_id_seq'),
                count(*) as "count",
                count(CASE WHEN is_spam = TRUE then TRUE ELSE NULL END)
            FROM
                (SELECT DISTINCT ON (group_id) * FROM hits_mv
                WHERE crawl_id = %s) AS p
            GROUP BY
                crawl_id, start_time
            """, row['id'])

            if i % commit_threshold == 0:
                print_status(i + 1, row['id'])
                transaction.commit_unless_managed()

        except:
            error_info = grab_error(sys.exc_info())
            log.error('an error occured at crawl_id: %s, %s %s' % (
                row['id'], error_info['type'], error_info['value']))
            execute_sql('rollback;')

    if i % commit_threshold != 0:
        print_status(i + 1, row['id'])
        transaction.commit_unless_managed()

    # delete dummy data
    execute_sql("DELETE FROM main_crawlagregates WHERE projects < 200;",
        commit=True)
    transaction.commit_unless_managed()


def get_crawls(start=None, end=None):
    """Returns dicts containing crawl ids."""
    st = time.time()
    log.debug("Fetching crawls to process.")
    extra_query = []
    start and end and extra_query.append(
        "p.start_time BETWEEN '{0}' AND '{1}'".format(
        start.isoformat(), end.isoformat()))
    query = """SELECT id FROM main_crawl p WHERE
        p.groups_available * {crawl_threshold} < p.groups_downloaded AND
        NOT EXISTS (SELECT id FROM main_crawlagregates WHERE crawl_id = p.id)
        {extra_limit}"""
    extra_qstr = ' AND ' + ' AND '.join(extra_query) if extra_query else ''
    query = query.format(extra_limit=extra_qstr,
        crawl_threshold=settings.INCOMPLETE_CRAWL_THRESHOLD)
    results = query_to_dicts(query)
    log.debug("Crawls fetched in {0}s.".format(time.time() - st))
    return results


def clear_existing_rows(start, end):
    t = time.time()
    log.info('Deleting crawl agregates for period {0} to {1}'.format(
        start, end))
    execute_sql("DELETE FROM main_crawlagregates WHERE start_time BETWEEN '{0}'"
        " and '{1}'".format(start.isoformat(), end.isoformat()), commit=True)
    log.info('Deleting crawl agregates for period {0} to {1} took {2}s.'.format(
        start, end, t))
