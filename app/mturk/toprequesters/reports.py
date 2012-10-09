import datetime
from django.core.cache import cache

from utils.sql import query_to_dicts
from utils.enum import EnumMetaclass


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
    return list(query_to_dicts("""
        SELECT
            h.requester_id,
            h.requester_name,
            count(DISTINCT hitgroup.group_id) as "projects",
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
        ORDER BY reward DESC
        LIMIT 1000;""".format(start_time.isoformat())))


def topreq_data_hits_posted(days):
    """Evaluates toprequesters by the number of hits posted in a period.

    Keyword arguments:
    days -- number of days to look back

    """
    start_time = datetime.date.today() - datetime.timedelta(int(days))

    # We are only interested in records having hits_posted > 0, thus only such
    # records will appear on the list and max(start_time) should be available at
    # all times.
    return list(query_to_dicts("""
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
        ORDER BY reward DESC
        LIMIT 1000;""".format(start_time.isoformat())))


class ToprequestersReport:
    """Enum representing available toprequesters reports."""

    __metaclass__ = EnumMetaclass

    cache_key_base = "TOPREQUESTERS_CACHED_"

    AVAILABLE = 0
    POSTED = 1

    display_names = {
        AVAILABLE: 'Hits available',
        POSTED: 'Hits posted',
    }

    REPORT_FUNCTION = {
        AVAILABLE: topreq_data_hits_available,
        POSTED: topreq_data_hits_posted,
    }

    @classmethod
    def get_cache_key(cls, report_type):
        """Returns string key, under which the report should be cached."""
        return cls.cache_key_base + str(report_type)

    @classmethod
    def __get_cache_key_for_meta(cls, report_type):
        """Returns string key, under which the report should be cached."""
        return cls.cache_key_base + str(report_type) + '_meta'

    @classmethod
    def is_cached(cls, report_type):
        """True is there is something under report key in the cache."""
        return cls.get_report_data(report_type) is not None

    @classmethod
    def get_report_data(cls, report_type):
        """Returns report data if available or None."""
        return cache.get(cls.get_cache_key(report_type))

    @classmethod
    def get_report_meta(cls, report_type):
        """Returns meta data related to the report."""
        return cache.get(cls.__get_cache_key_for_meta(report_type))

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
            meta = cls.get_report_meta(rid)
            if meta:
                meta = (' ({0} days), updated: {1:%Y-%m-%d %H:%M:%S}, elapsed:'
                ' {2}s').format(meta.get('days'), meta.get('start_time'),
                                int(meta.get('elapsed')))
            else:
                meta = ''
            lines.append("\n{0} {1} - {2}{3}".format(in_cache, rid, name, meta))
        lines.append('\n')
        return ''.join(lines)

    @classmethod
    def store(cls, report_type, data, meta=None, cache_expiry=60 * 60 * 4):
        """Stores the data under correct cache key.

        Keyword arguments:

        report_type -- type of the report to relate the data to
        data -- report data
        meta -- report meta data
        cache_expiry -- how long the data should remain in cache

        """
        cls.__store_meta(report_type, meta, cache_expiry)
        return cache.set(cls.get_cache_key(report_type), data, cache_expiry)

    @classmethod
    def __store_meta(cls, report_type, meta, cache_expiry):
        """Stores meta data. Adding this method to allow manual update of
        reports meta data.

        """
        return cache.set(
            cls.__get_cache_key_for_meta(report_type), meta, cache_expiry)

    @classmethod
    def purge(cls, report_type):
        """Deletes all the data related to the given report type from cache."""
        return cache.delete(cls.get_cache_key(report_type))
