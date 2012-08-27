import logging
import resource

from datetime import date, datetime, timedelta
from optparse import make_option

from django.core.management.base import BaseCommand

from utils.sql import execute_sql
from mturk.main.models import HitGroupClassAggregate


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger(__name__)


class CalculateClassAggregates(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("--erase", dest="erase", action="store_true",
                    default=False),
        make_option("--clear", dest="clear", action="store_true",
                    default=False),
        make_option("--day", dest="day", action="store",
                    default=None),
        make_option("--begin", dest="begin", action="store",
                    default=None),
        make_option("--end", dest="end", action="store",
                    default=None)
    )

    def handle(self, *args, **options):

        if options["erase"]:
            HitGroupClassAggregate.objects.all().delete()
            return

        day = options["day"]
        begin = options["begin"]
        end = options["end"]

        if day is not None:
            begin = datetime(date)
            end = datetime(date + timedelta(days=1))

        queryset = HitGroupClassAggregate.objects.filter(
                start_time__gte=begin,
                start_time__lt=end)
        if options["clear"]:
            queryset.delete()

        if queryset.exists():
            logger.error("Some of aggreagates are already calucated for a "
                         "given time interval")
            return

        logger.info("Making hit group class aggregates from {} to {}"
                    .format(begin, end))
        query = """
            INSERT INTO main_hitgroupclassaggregate
                        (crawl_id, start_time, classes, hits_available)
                SELECT crawl_id, start_time, classes,
                       sum(hits_available) as hits_available
                FROM hits_mv
                JOIN main_hitgroupclass
                ON hits_mv.group_id = main_hitgroupclass.group_id
                WHERE start_time >= '{}' AND start_time < '{}'
                GROUP BY crawl_id, start_time, classes;
            """.format(begin, end)
        execute_sql(query, commit=True)

        logger.info("Hit group class aggregates are made")


Command = CalculateClassAggregates
