import sys
import time
import logging
from optparse import make_option

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
        make_option("--count_only", dest="count_only",
            default=False, action="store_true",
            help="Command will print the number of records requiring"
            " processing and exit."),
        make_option("--chunk_size", dest="chunk_size", type="int",
            default=500, help="Chunk size for the chunked delete mode."),
        make_option("--simple", dest="simple",
            default=False, action="store_true",
            help="If set to true, the data will not be batch deleted, using "
            "'=' instead of 'in' operator."),
    )
    help = "Removes data related to bad crawls."

    def handle(self, **options):

        pid = Pid('clear_bad_crawl_related', True)

        self.count_only(options.get('count_only'))

        start_time = time.time()
        limit = options.get('limit')
        crawl_count = self.get_crawls_count()

        # if limit is specified, show X/Y instead of just Y
        log.info('Starting bad crawl related data removal, {0}{1} records will '
            'be processed.'.format('{0}/'.format(limit) if limit else '',
            crawl_count))

        ids = self.get_crawl_ids()
        deleted = self.do_deletes(
            not options.get('simple'), options.get('chunk_size'),
            ids, crawl_count, limit)

        log.info('Command took: {0}, {1} crawls processed.'.format(
            time.time() - start_time, deleted))

        pid.remove_pid()

    crawls_query = """
    SELECT {what} FROM main_crawl
    WHERE has_hits_mv = true AND groups_available * 0.9 < groups_downloaded
    {ordering};
    """

    def count_only(self, count_only):
        """Handles the count_only option."""
        if count_only:
            msg = '{0} records must be processed.'.format(
                self.get_crawls_count())
            print msg
            log.info(msg)
            sys.exit(0)

    def get_crawl_ids(self):
        """Returns an iterator containing the ids of records to delete."""
        return query_to_tuples(self.crawls_query.format(
            what='id', ordering="ORDER BY start_time DESC"))

    def get_crawls_count(self):
        """Counts the records to delete."""
        return [a for a in query_to_tuples(self.crawls_query.format(
            what='count(*)', ordering=""))][0][0]

    #
    # Deleting
    #
    def do_deletes(self, chunked=True, chunk_size=None, *args, **kwargs):
        if chunked:
            return self.do_deletes_chunked(*args, **kwargs)
        else:
            return self.do_deletes_simple(*args, **kwargs)

    def do_deletes_simple(self, ids, total_len, limit=None):
        """Simple version - each query is ran once per crawl."""
        qs = self._get_delete_queries('=')
        for i, (crawl_id, ) in enumerate(ids, start=1):
            if limit and i > limit:
                break
            for q in qs:
                execute_sql(q.format(crawl_id))
            if i % 50 == 0:
                log.info("{0}/{1} crawls processed.".format(i, total_len))
            execute_sql(("update main_crawl set has_hits_mv = false where"
                " id = {0};").format(crawl_id))

        execute_sql("COMMIT;")
        return i

    def read_chunks(self, iterator, chunk_size=100, limit=None):
        """Returns a list of next ``chunk_size`` elements, up to ``limit``
        total from given ``iterator``.
        """
        items = list()
        for i, (crawl_id, ) in enumerate(iterator, start=1):
            if limit and i > limit:
                break
            items.append(crawl_id)
            if len(items) == chunk_size:
                yield items
                items = list()
        if items:
            yield items

    def do_deletes_chunked(self, ids, total_len, limit=None, chunk_size=None):
        """More complex version, does multiple crawls at a time."""
        processed = 0
        qs = self._get_delete_queries('in')
        for chunk in self.read_chunks(ids, limit=limit, chunk_size=chunk_size):
            chunk_str = "({0})".format(", ".join([str(a) for a in chunk]))
            for q in qs:
                execute_sql(q.format(chunk_str))
            execute_sql(("update main_crawl set has_hits_mv = false where"
                " id in {0};").format(chunk_str))
            processed += len(chunk)
            log.info("{0}/{1} crawls processed.".format(processed, total_len))

        execute_sql("COMMIT;")
        return processed

    def _get_delete_queries(self, comparator='='):
        """Returns delete queries for all related tables, cmparator argument can
        be used to get 'crawl_id =' or 'crawl_id in' queries.
        """
        for t in ['hits_mv', 'main_crawlagregates', 'hits_temp']:
            yield "delete from {0} where crawl_id {1} {{0}};".format(
                t, comparator)
