import time
import datetime
import pytz
from pprint import pprint
from django.utils.timezone import now, make_aware
from mturk.main.models import Crawl, HitGroupContent


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
            dev = None
            if (c.groups_available > 0 and c.groups_downloaded is not None):
                dev = (c.groups_available - c.groups_downloaded
                    ) * 100 / c.groups_available
                dev = '{0}% !!!'.format(dev) if dev > 10 else dev
            pprint((c.start_time.hour, c.start_time.minute, c.groups_available,
                c.groups_downloaded, c.hitgroupstatus_set.count(), dev))
        time.sleep(sleep)


def get_unavailable_group_ids_percent(period=30, periods=40):
    results = []
    today = now().date()
    today -= datetime.timedelta(days=today.day)
    for dt in datetime_range(today, period=period, periods=periods):
        dte = dt + datetime.timedelta(days=period)
        items = HitGroupContent.objects.filter(
            first_crawl__start_time__gt=dt, first_crawl__start_time__lt=dte
            ).only('group_id_hashed')
        hashed = len([i for i in items if i.group_id_hashed])
        percent = float(hashed) / len(items) * 100 if len(items) != 0 else 0
        results.append((dt, percent))
        print "{0} {1}".format(*results[-1])
    return results


def get_first_crawl_hits_posted_sums(days=200):
    results = []
    for i, dt in enumerate(datetime_range(now().date(), periods=days), start=1):
        tt = time.time()
        result = sum([
            sum([
                crawl.hitgroupstatus_set.get(hit_group_content__id=content.id
                ).hits_available for content in  crawl.hitgroupcontent_set.all()
            ]) for crawl in
                Crawl.objects.filter(
                    start_time__gt=dt,
                    start_time__lt=dt + datetime.timedelta(days=1))
        ])
        results.append((dt, result))
        print '{0}. {1} - {2}, {3}s elapsed'.format(
            i, dt, result, time.time() - tt)
    return results


def convert_date_to_aware_utc_datetime(dt):
    return make_aware(datetime.datetime.combine(dt, datetime.time(0)), pytz.UTC)


def datetime_range(start=now(), period=1, periods=30):
    return [convert_date_to_aware_utc_datetime(
        start - datetime.timedelta(days=period * x)) for x in range(0, periods)]
