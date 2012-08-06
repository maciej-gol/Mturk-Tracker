import datetime
from django.core.cache import cache

from utils.sql import query_to_tuples, execute_sql

# TODO2: ADD EnumMetaClass to the project


def topreq_data_hits_available(days):
    """Evaluates toprequesters by the number of hits available as an average
    over the time period.

    Keyword arguments:
    days -- number of days to look back

    """
    start_time = datetime.date.today() - datetime.timedelta(int(days))

    # We are only interested in records having hits_posted > 0, thus only such
    # records will appear on the list and max(start_time) should be available at
    # all times.
    return list(query_to_tuples("""
        SELECT
            h.requester_id,
            h.requester_name,
            coalesce(count(*), 0) as "projects",
            coalesce(round(CAST (sum(hitgroup.grp_hits) as NUMERIC), 0), 0) as hits,
            coalesce(sum(hitgroup.grp_hits * h.reward), 0) as reward,
            max(hitgroup.grp_last_posted) as "last_posted"
        FROM
            main_hitgroupcontent h
            LEFT JOIN main_requesterprofile p
                ON h.requester_id = p.requester_id
            LEFT JOIN (
            SELECT
                mv.group_id,
                coalesce(avg(mv.hits_available), 0) as "grp_hits",
                max(mv.start_time) as "grp_last_posted"
            FROM (
                SELECT group_id, hits_available, start_time
                FROM hits_mv
                WHERE
                    start_time > '{0}'
                ) mv
                GROUP BY mv.group_id
            ) hitgroup
                ON h.group_id = hitgroup.group_id
            WHERE
                coalesce(p.is_public, true) = true
            GROUP BY h.requester_id, h.requester_name
            ORDER BY reward desc;""".format(start_time.isoformat())))


def topreq_data_hits_posted(days):
    """Evaluates toprequesters by the number of hits posted in a period.

    Keyword arguments:
    days -- number of days to look back

    """
    start_time = datetime.date.today() - datetime.timedelta(int(days))

    # We are only interested in records having hits_posted > 0, thus only such
    # records will appear on the list and max(start_time) should be available at
    # all times.
    return list(query_to_tuples("""
        SELECT
            h.requester_id,
            h.requester_name,
            coalesce(count(distinct mv.group_id), 0) as "projects",
            coalesce(sum(mv.hits_posted), 0) as "hits",
            coalesce(sum(mv.hits_posted * h.reward), 0) as "reward",
            max(mv.start_time) as "last_posted"
        FROM
            main_hitgroupcontent h
            LEFT JOIN main_requesterprofile p
                ON h.requester_id = p.requester_id
            LEFT JOIN (
                SELECT group_id, hits_posted, start_time
                FROM hits_mv
                WHERE
                    start_time > '{0}' AND
                    hits_posted > 0
            ) mv
                ON h.group_id = mv.group_id
            WHERE
                coalesce(p.is_public, true) = true
            GROUP BY h.requester_id, h.requester_name
            ORDER BY reward desc;""".format(start_time.isoformat())))


def topreq_data_hits_posted_crawl_id(days):
    """Evaluates toprequesters by the number of hits posted in a period.

    Keyword arguments:
    days -- number of days to look back

    """
    # select the first crawl considered by start_time
    firstcrawl = execute_sql("""
        SELECT crawl_id
        FROM hits_mv
        WHERE
            start_time > %s
        ORDER BY start_time ASC
        LIMIT 1;""", datetime.date.today() - datetime.timedelta(int(days))
        ).fetchall()[0][0]

    # We are only interested in records having hits_posted > 0, thus only such
    # records will appear on the list and max(start_time) should be available at
    # all times.
    return list(query_to_tuples("""
        SELECT
            h.requester_id,
            h.requester_name,
            coalesce(count(distinct mv.group_id), 0) as "projects",
            coalesce(sum(mv.hits_posted), 0) as "hits",
            coalesce(sum(mv.hits_posted * h.reward), 0) as "reward",
            max(mv.start_time) as "last_posted"
        FROM
            main_hitgroupcontent h
            LEFT JOIN main_requesterprofile p
                ON h.requester_id = p.requester_id
            LEFT JOIN (
                SELECT group_id, hits_posted, start_time
                FROM hits_mv
                WHERE
                    crawl_id > {0} AND
                    hits_posted > 0
            ) mv
                ON h.group_id = mv.group_id
            WHERE
                coalesce(p.is_public, true) = true
            GROUP BY h.requester_id, h.requester_name
            ORDER BY reward desc;""".format(firstcrawl)))


class ToprequestersReport:
    """Enum representing available toprequesters reports."""

    #TODO: Add EnumMetaClass to the project and replace repetitive code below
    #TODO2: Test and remove the long-named option
    #TODO3: Add store_report_data method
    cache_key_base = "TOPREQUESTERS_CACHED_"

    AVAILABLE = 0
    POSTED = 1
    POSTED_CRAWL_ID_QUERY_VARIANT = 2

    values = [
        AVAILABLE,
        POSTED,
        POSTED_CRAWL_ID_QUERY_VARIANT
    ]
    display_names = {
        AVAILABLE: 'Hits available',
        POSTED: 'Hits posted',
        # TODO remove once we are sure it's slower:
        POSTED_CRAWL_ID_QUERY_VARIANT: 'Hits posted (crawl id query variant)',
    }

    REPORT_FUNCTION = {
        AVAILABLE: topreq_data_hits_available,
        POSTED: topreq_data_hits_posted,
        POSTED_CRAWL_ID_QUERY_VARIANT: topreq_data_hits_posted_crawl_id,
    }

    @classmethod
    def get_cache_key(cls, report_type):
        """Returns string key, under which the report should be cached."""
        return cls.cache_key_base + str(report_type)

    @classmethod
    def is_cached(cls, report_type):
        """True is there is something under report key in the cache."""
        return cls.get_report_data(report_type) is not None

    @classmethod
    def get_report_data(cls, report_type):
        """Returns report data if available or None."""
        return cache.get(cls.get_cache_key(report_type))

    @classmethod
    def get_available_as_str(cls):
        """Returns a string consising of lines:

            [available] id - Display name

        Example:

            [x] 0 - Hits available
            [ ] 1 - Hits posted

        """
        lines = []
        for rid, name in cls.display_names.iteritems():
            in_cache = cls.is_cached(rid)
            in_cache = '[x]' if in_cache else '[ ]'
            lines.append("\n{0} {1} - {2}".format(in_cache, rid, name))
        lines.append('\n')
        return ''.join(lines)

    @classmethod
    def store(cls, report_type, data, cache_expiry=60 * 60 * 4):
        """Stores the data under correct cache key."""
        return cache.set(cls.get_cache_key(report_type), data, cache_expiry)

    @classmethod
    def purge(cls, report_type):
        """Deletes all the data related to the given report type from cache."""
        return cache.delete(cls.get_cache_key(report_type))
