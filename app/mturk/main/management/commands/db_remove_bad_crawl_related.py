import time
import logging
from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand
from utils.pid import Pid
from utils.sql import query_to_tuples, execute_sql

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Clears hits_mv, hits_temp and main_crawlagregates entries related to
    crawls with not enough hits_downloaded and sets has_hits_mv to null.

    Command can run in two modes:
    * simple -- removing related objects in a single statement per crawl
    * chunked -- back processing groups of crawls using 'in' comparison.

    """

    option_list = BaseCommand.option_list + (
        make_option("--limit", dest="limit", type="int",
            help="Number of crawls to process."),
        make_option("--count-only", dest="count-only",
            default=False, action="store_true",
            help="Command will print the number of records requiring"
            " processing and exit."),
        make_option("--all", dest="all", default=False, action="store_true",
            help="Decides if crawls with has_hits_mv=False should be included, "
            "use to filter out already processed records."),
    )
    help = "Removes data related to bad crawls."

    def handle(self, **options):

        pid = Pid('clear_bad_crawl_related', True)

        self.having_hits_mv = not options.get('all')

        start_time = time.time()
        self.crawl_count = self.get_crawls_count()

        if options.get('count-only') or self.crawl_count == 0:
            print '{0} records to process.'.format(self.crawl_count)
            return

        limit = options.get('limit')

        # if limit is specified, show X/Y instead of just Y
        log.info('Starting bad crawl related data removal, {0}{1} records will '
            'be processed.'.format('{0}/'.format(limit) if limit else '',
            self.crawl_count))

        ids = self.get_crawl_ids()
        deleted = self.do_deletes(ids, self.crawl_count, limit)

        log.info('Command took: {0}, {1} crawls processed.'.format(
            time.time() - start_time, deleted))

        pid.remove_pid()

    def get_crawl_ids(self):
        """Returns an iterator containing the ids of records to delete."""
        return query_to_tuples(self.__get_crawls_query())

    def get_crawls_count(self):
        """Counts the records to delete."""
        return [a for a in query_to_tuples(self.__get_crawls_query(
            count_only=True))][0][0]

    crawls_query = """
    SELECT {what} FROM main_crawl
    WHERE {having_hits_mv} groups_available * 0.9 > groups_downloaded
    {ordering}
    """

    def __get_crawls_query(self, what='id', ordered=True, count_only=False):
        if count_only:
            ordered = False
            what = 'count(*)'
        ordering = "ORDER BY start_time DESC" if ordered else ""
        hmv = 'has_hits_mv is true AND' if self.having_hits_mv else ''
        return self.crawls_query.format(what=what, ordering=ordering,
            having_hits_mv=hmv)

    #
    # Deleting
    #
    def do_deletes(self, ids, total_len, limit=None):
        """Executes a delete query for each related table per crawl."""
        qs = self._get_delete_queries()
        for i, (crawl_id, ) in enumerate(ids, start=1):
            if limit and i > limit:
                break
            for q in qs:
                execute_sql(q.format(crawl_id))
            if i % 1000 == 0:
                log.info("{0}/{1} crawls processed, commiting.".format(
                    i, total_len))
                transaction.commit_unless_managed()
            execute_sql(("update main_crawl set has_hits_mv = false where"
                " id = {0}").format(crawl_id))

        transaction.commit_unless_managed()
        return i

    delete_tables = ['hits_mv', 'main_crawlagregates', 'hits_temp']

    def _get_delete_queries(self):
        """Returns delete queries for all related tables."""
        return ["delete from {0} where crawl_id = {{0}}".format(t) for
            t in self.delete_tables]
