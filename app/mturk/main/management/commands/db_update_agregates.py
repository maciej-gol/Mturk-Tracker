# -*- coding: utf-8 -*-
import time
import logging

from django.core.management.base import BaseCommand

from utils.pid import Pid

from mturk.main.management.commands import update_crawl_agregates


log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refreshes materialised views used to generate stats'

    def handle(self, **options):

        pid = Pid('mturk_agregates', True)
        start_time = time.time()

        log.info('Updating crawl agregates')
        update_crawl_agregates(only_new=True)

        log.info('db_update_agregates took: %s' % (time.time() - start_time))

        pid.remove_pid()
