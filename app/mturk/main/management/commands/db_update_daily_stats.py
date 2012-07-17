import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from mturk.main.models import Crawl, DayStats, CrawlAgregates

log = logging.getLogger(__name__)


def get_first_crawl():
        crawls = Crawl.objects.filter().order_by('start_time')[:1]
        if not crawls:
            return None
        else:
            return crawls[0]


class Command(BaseCommand):

    help = 'Calculates daily stats'

    def handle(self, **options):
        """Updates daily stats by reducing hitgroups_posted and
        hitgroups_consumed of CrawAggregates occuring that day.

        """
        commit_every = 100
        crawl = get_first_crawl()
        if not crawl:
            log.error("No crawls to process.")
            return

        transaction.enter_transaction_management()
        transaction.managed(True)
        updates, creates = (0, 0)

        start, end = (crawl.start_day(), datetime.date.today())
        days = (end - start).days
        log.info("Processing {0} to {1} ({2} days).".format(start, end, days))
        i = 0
        for i in range(0, days):

            day = crawl.start_day() + datetime.timedelta(days=i)
            day_end = day + datetime.timedelta(days=1)

            # excluding objects having zero
            aggregates = CrawlAgregates.objects.filter(
                start_time__gte=day, start_time__lt=day_end
                ).filter(Q(hitgroups_posted__gt=0) |
                         Q(hitgroups_consumed__gt=0))

            if len(aggregates) == 0:
                log.info("No crawl aggregates for %s." % day)
                continue

            res = [0, 0, 0, 0]
            for a in aggregates:
                for i, at in enumerate(['hitgroups_posted', 'rewards_posted',
                    'hitgroups_consumed', 'rewards_consumed']):
                    res[i] += getattr(a, at) or 0
            values = {}
            for i, k in enumerate(['arrivals', 'arrivals_value', 'processed',
                'processed_value']):
                values[k] = res[i]

            obj, created = DayStats.objects.get_or_create(
                date=day, defaults=values)

            if not created:
                updated = False
                for k, v in values.iteritems():
                    if (v is not None and
                        round(getattr(obj, k), 4) != round(v, 4)):
                        setattr(obj, k, v)
                        updated = True
                if updated:
                    obj.save()
                    updates += 1
            else:
                creates += 1

            if i % commit_every == 0:
                log.info('{0}/{1} days processed, commiting.'.format(i, days))
                transaction.commit()

        # commit the missing records
        if i % commit_every != 0:
            log.info('{0}/{1} days processed, commiting.'.format(i, days))
            transaction.commit()

        log.info('DayStat refresh finished: {0}/{1}/{2} created/updated/total '
            'objects.'.format(creates, updates, days))
