import time
import logging
from optparse import make_option
from django.db import transaction
from django.conf import settings

from utils.pid import Pid
from utils.sql import execute_sql, query_to_tuples
from utils.management.commands.base.time_args_command import TimeArgsCommand

log = logging.getLogger('mturk.aggregates')


class Command(TimeArgsCommand):

    help = 'Refreshes materialised views aggregates.'

    option_list = TimeArgsCommand.option_list + (
        make_option("--clear-existing", dest="clear-existing",
            default=True, action="store_false",
            help='If true, related hits_mv record will be deleted prior to '
                'update.'),
        make_option("--force", dest="force",
            default=False, action="store_true",
            help='If true, query will ignore has_hits_mv and related'
                'main_crawlagregates rows when querying for crawls.'
                'This option requires time interval to be specified.'),
    )

    def process_options(self, options):
        super(Command, self).process_options(options)
        self.clear_existing = self.options['clear-existing']
        self.force = self.options['force']
        assert(self.start and self.end if self.force else True)

    def handle(self, **options):

        pid = Pid('mtur_aggregates')

        self.process_options(options)
        start_time = time.time()

        log.info('Refreshing hits_mv')
        update_mviews(clear_existing=self.clear_existing, force=self.force,
            start=self.start, end=self.end)
        log.info('Done refreshing hits_mv db_refresh_mviews took: {0}s.'.format(
            time.time() - start_time))

        pid.remove_pid()


def update_mviews(clear_existing=True, force=False, start=None, end=None):
    """Creates hits_mv records for crawls with enough groups_downloaded
    taking data from main_hitgroupstatus and main_hitgroupcontent tables.

    Filtering out incomplete anonymous crawls
    -----------------------------------------
    Note: this is covered by the latter case

    There is a 20 page limit for anonymous mturk.com users, each page having
    10 hitgroups, while usual number of hitgroups is at least 100.
    Thus all crawls with 200 or less crawls should be excluded.

    Filtering erronous crawls
    -------------------------
    Usually, the difference between hitgroups_downloaded and higroups_available
    exceeding 10 percent denotes a crawl error. Such crawls should be excluded
    from creating hits_mv and further table records.

    """
    for crawl_id, start_time in get_crawls_for_update(force, start, end):

        if clear_existing:
            log.info("Deleting hits_mv records for: {0}".format(crawl_id))
            execute_sql("DELETE FROM hits_mv WHERE crawl_id = {0}".format(
                crawl_id), commit=True)

        log.info("Creating hits_mv records for: {0}.".format(crawl_id))
        create_hits_mv_record(start_time, crawl_id)


def get_crawls_for_update(force=False, start=None, end=None):
    """Returns (id, start_time) tuples of crawls to update.

    Keyword arguments:
    start, end -- define the time interval to pick crawls from
    forced -- decides whether has_hits_mv should be respected

    """
    # build query args
    extra_query = []
    start and end and extra_query.append(
        "start_time BETWEEN '{0}' AND '{1}'".format(
        start.isoformat(), end.isoformat()))
    not force and extra_query.append("has_hits_mv = false")
    extra_qstr = ' AND ' + ' AND '.join(extra_query) if extra_query else ''
    query = """SELECT
        id, start_time FROM main_crawl p
    WHERE
        p.success = true AND
        old_id is null AND
        p.groups_available * {0} < p.groups_downloaded AND
        NOT EXISTS (SELECT id FROM main_crawlagregates WHERE crawl_id = p.id)
        {extra_query}
    ORDER BY id DESC""".format(settings.INCOMPLETE_CRAWL_THRESHOLD)
    return query_to_tuples(query.format(extra_query=extra_qstr))


def create_hits_mv_record(start_time, crawl_id):
    """Aggregates main_hitgroupstatus/main_hitgroupcontent data into hits_mv
    and marks crawl as already processed."""
    execute_sql("""INSERT INTO
            hits_mv (status_id, content_id, group_id, crawl_id, start_time,
                requester_id, hits_available, page_number, inpage_position,
                hit_expiration_date, reward, time_alloted, hits_diff,
                is_spam)
        SELECT p.id AS status_id, q.id AS content_id, p.group_id,
            p.crawl_id, TIMESTAMP '{start_time}',
            q.requester_id, p.hits_available, p.page_number,
            p.inpage_position, p.hit_expiration_date, q.reward,
            q.time_alloted, null, q.is_spam
        FROM
            main_hitgroupstatus p
        JOIN
            main_hitgroupcontent q ON (q.group_id::text = p.group_id::text
                                       AND p.hit_group_content_id = q.id)
        WHERE
            p.crawl_id = {crawl_id};
    """.format(start_time=start_time, crawl_id=crawl_id), commit=True)

    execute_sql(("UPDATE main_crawl SET has_hits_mv = true WHERE id = {0};"
        ).format(crawl_id), commit=True)

    transaction.commit_unless_managed()
