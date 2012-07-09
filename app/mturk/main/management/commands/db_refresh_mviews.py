import time
import logging

from django.core.management.base import BaseCommand

from utils.pid import Pid

from mturk.main.management.commands import clean_duplicates, update_mviews


log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refreshes materialised views used to generate stats'

    def handle(self, **options):

        pid = Pid('mturk_crawler', True)

        start_time = time.time()

        log.info('Removing duplicate hitgroupcontent and hitgroupstatuses.')
        clean_duplicates()

        log.info('Refreshing hits_mv')
        update_mviews()

        log.info('Done refreshing hits_mv')

        log.info('db_refresh_mviews took: %s' % (time.time() - start_time))

        pid.remove_pid()
