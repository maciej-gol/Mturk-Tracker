import time
import datetime
from pprint import pprint
from django.utils.timezone import now
from mturk.main.models import Crawl


def print_crawls(age=datetime.timedelta(hours=2), sleep=15, limit=None):
    """Script for displaying latest crawls and their details."""

    while True:
        crawls = Crawl.objects.filter(start_time__gt=now() - age
            ).order_by('start_time')
        if limit:
            crawls = crawls[:limit]
        print '------------------------------------'
        print '(H, M, avail, down, statuses, dev %)'
        print '------------------------------------'
        for c in crawls:
            dev = (c.groups_available - c.groups_downloaded
                ) * 100 / c.groups_available
            dev = '[{0}] !!!'.format(dev) if dev > 10 else dev
            pprint((c.start_time.hour, c.start_time.minute, c.groups_available,
                c.groups_downloaded, c.hitgroupstatus_set.count(), dev))
        time.sleep(sleep)
