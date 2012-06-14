import time
import logging

from django.core.management.base import BaseCommand, NoArgsCommand
from optparse import make_option
from utils.pid import Pid
from mturk.main.models import Crawl

from mturk.main.management.commands.diffs import update_cid
from django.db import transaction

log = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--limit', dest='limit', default='100', type='int',
            help='Number of crawls to process.'),
    )
    help = 'Update views with diff values'

    def handle(self, **options):

        pid = Pid('mturk_diffs', True)

        transaction.enter_transaction_management()
        transaction.managed(True)

        start_time = time.time()

        try:

            items = Crawl.objects.filter(is_spam_computed=False
                ).order_by('-id')[:options['limit']]
            lenitems = len(items)

            log.info(('Starting db_update_diffs, {0} crawls will be updated.'
                ).format(lenitems))

            for c in items:

                updated = update_cid(c.id)

                if updated > 0:
                    c.has_diffs = True
                    c.save()

                transaction.commit()

        except (KeyError, KeyboardInterrupt) as e:
            log.info(('Exception, rolling back the transaction and exiting: {0}'
                ).format(e))
            transaction.rollback()
            pid.remove_pid()
            exit()

        log.info('Success! Updating {0} crawls took: {1} s'.format(
            lenitems, time.time() - start_time))
