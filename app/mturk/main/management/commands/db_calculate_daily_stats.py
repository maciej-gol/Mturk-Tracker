import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from utils.sql import query_to_dicts
from mturk.main.models import Crawl, DayStats

log = logging.getLogger(__name__)


def get_first_crawl():
        crawls = Crawl.objects.filter(has_diffs=True).order_by('start_time')[:1]
        if not crawls:
            return None
        else:
            return crawls[0]


class Command(BaseCommand):

    help = 'Calculates daily stats'

    def handle(self, **options):

        """
        take all crawls that have diffs computed from - inf till yesterday
        start from the oldest crawl and try to create daily stats
        if there are some crawls without diffs stop the process
        """

        '''
        take earliest crawl
        calculate incosistencies in history
        calculate data for every missing element
        '''
        crawl = get_first_crawl()
        if not crawl:
            log.error("No crawls to process.")
            return

        transaction.enter_transaction_management()
        transaction.managed(True)
        created = 0

        start, end = (crawl.start_day(), datetime.date.today())
        days = (end - start).days
        log.info("Processing {0} to {1} ({2} days).".format(start, end, days))

        for i in range(0, days):

            day = crawl.start_day() + datetime.timedelta(days=i)
            day_end = day + datetime.timedelta(days=1)

            crawls = Crawl.objects.filter(has_diffs=False, start_time__gte=day,
                start_time__lt=day_end)
            if len(crawls) > 0:
                log.error("Not all crawls from %s have diffs." % day)
                continue

            try:
                DayStats.objects.get(date=day)
            except DayStats.DoesNotExist:
                log.info("Calculating stats for %s" % day)

                range_start_date = day.isoformat()
                range_end_date = (day_end).isoformat()

                log.info("Calculating arrivals.")
                '''
                stats for projects posted on particular day
                '''
                arrivals = query_to_dicts('''
                    select
                        sum(hits_diff) as "arrivals",
                        sum(hits_diff*reward) as "arrivals_value"
                    from
                        hits_mv p
                    where
                     start_time between TIMESTAMP '%s' and TIMESTAMP '%s'
                        and hits_diff > 0
                    ''' % (range_start_date, range_end_date)).next()
                if arrivals['arrivals'] == None:
                    log.info('Arrivals is None, skipping.')
                    continue

                log.info("Calculating processed.")
                processed = query_to_dicts('''
                    select
                        sum(hits_diff) as "processed",
                        sum(hits_diff*reward) as "processed_value"
                    from
                        hits_mv p
                    where
                     start_time between TIMESTAMP '%s' and TIMESTAMP '%s'
                        and hits_diff < 0
                    ''' % (range_start_date, range_end_date)).next()
                if processed['processed'] == None:
                    log.info('Processed is None, skipping.')
                    continue

                DayStats.objects.create(date=day,
                    arrivals=arrivals['arrivals'],
                    arrivals_value=arrivals['arrivals_value'],
                    processed=processed['processed'],
                    processed_value=processed['processed_value'])
                created += 1
                transaction.commit()

        log.info('Finish: {0} DayStat objects were created.'.format(created))
