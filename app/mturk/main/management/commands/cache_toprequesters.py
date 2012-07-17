import time
import logging
from django.core.cache import cache
from utils.pid import Pid

from django.core.management.base import BaseCommand, NoArgsCommand
from optparse import make_option


HOURS4 = 60 * 60 * 4

log = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--days', dest='days', default='30',
            help='Number of days from which the history data is grabbed.'),
        make_option('--force', dest='force', action="store_true", default=False,
            help='Enforces overriding existing entry in the cache.'),
    )
    help = 'Make sure top requesters are in cache.'

    def handle(self, **options):

        pid = Pid('mturk_cache_topreq', True)

        key = 'TOPREQUESTERS_CACHED'

        result = cache.get(key)
	force = options['force']
        if result is not None and not force:
            log.info("toprequesters still in cache...")
            return
	
	if not force:
            log.info("toprequesters missing, refetching")
        else:
            log.info("refetching toprequesters")

        days = options['days']
        # no chache perform query:
        from mturk.main.views import topreq_data
        start_time = time.time()
        data = topreq_data(days)
        log.info("toprequesters: filled memcache in %s", time.time() - start_time)
        cache.set(key, data, HOURS4)

        pid.remove_pid()
