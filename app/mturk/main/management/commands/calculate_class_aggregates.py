import logging
import resource

from datetime import date, datetime, timedelta
from optparse import make_option

from django.core.management.base import BaseCommand

from utils.sql import query_to_dicts


# Set limit for avaliable resources.
resource.setrlimit(resource.RLIMIT_AS, (2048 * 1048576L, -1L))
logger = logging.getLogger(__name__)

class CalculateClassAggregates(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("--verbose", dest="verbose", action="store_true",
                    default=False, help=u"print more messages"),
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

        day = options["day"]
        begin = options["begin"]
        end = options["end"]

        if day is not None:
            begin = datetime(date)
            end = datetime(date + timedelta(days=1))

        print "Making hit group class aggregates from {} to {}".format(begin, end)

        query_to_dicts("""
            INSERT INTO main_hitgroupclassaggregate
                SELECT crawl_id, start_time, classes, sum(hits_available) as hits_available
                FROM hits_mv
                JOIN main_hitgroupclass
                ON hits_mv.group_id = main_hitgroupclass.group_id 
                WHERE start_time >= '{}' AND start_time <= '{}' 
                GROUP BY crawl_id, start_time, classes;
            """.format(begin, end))

        print "Hit group class aggregates made"
                

Command = CalculateClassAggregates 
