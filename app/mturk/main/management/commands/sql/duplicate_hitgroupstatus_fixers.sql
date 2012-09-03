-- This should be one-time problem since the crawls are now patched and
-- duplicate hitgroupstatuses should not appear.

-- Removes hitgroupstatus duplicates
DELETE FROM main_hitgroupstatus mh
USING (
    SELECT group_id, crawl_id, min(id) AS id FROM main_hitgroupstatus
    WHERE
        crawl_id > (
            SELECT id FROM main_crawl
            WHERE start_time BETWEEN '2012-01-01' AND '2013-01-01'
            ORDER BY start_time ASC LIMIT 1
        ) AND
        crawl_id < (
            SELECT id FROM main_crawl
            WHERE start_time BETWEEN '2012-01-01' AND '2013-01-01'
            ORDER BY start_time DESC LIMIT 1
        )
    GROUP BY crawl_id, group_id
    HAVING count(*) > 1
) AS asd
WHERE
    mh.crawl_id = asd.crawl_id AND
    mh.group_id = asd.group_id AND
    mh.id != asd.id;

-- for; 2012-01-01 to 2012-08-15'
-- DELETE 1146569
-- Time: 2480477.275 ms

-- Removes hits_mv related to removed main_hitgroupstatus
DELETE FROM hits_mv
USING (
    SELECT mhs.id as id
    FROM hits_mv
    LEFT OUTER JOIN (
            SELECT id
            FROM main_hitgroupstatus
            WHERE crawl_id >= (
                SELECT min(id) FROM main_crawl
                WHERE start_time > '2012-01-01'
            ) AND
            crawl_id <= (
                SELECT max(id) FROM main_crawl
                WHERE start_time < '2013-01-01'
            )
        ) mhs
        ON hits_mv.status_id = mhs.id
    WHERE mhs.id is null
) as missing;
WHERE
    hits_mv.status_id = missing.id

-- Count hits_mv related to missing main_hitgroupstatus
SELECT count(*)
FROM (
    SELECT main_hitgroupstatus.id as id
    FROM hits_mv
    LEFT OUTER JOIN main_hitgroupstatus
        ON hits_mv.status_id = main_hitgroupstatus.id
    WHERE main_hitgroupstatus.id is null
) as asd;

-- for; 2012-01-01 to 2012-08-15'
-- 1603847.209 ms


-- Counts the number of groups that'll be corrected and the number of deleted
-- items. They differ since there can be more than one extra status per group,
-- crawl pair.
select count(*) as corrected, sum(asd.extra - 1) as removed from (
    select group_id, crawl_id, count(*) as extra, min(id) as id
    from main_hitgroupstatus
    where
        crawl_id > (
            SELECT id FROM main_crawl
            WHERE start_time BETWEEN '2012-01-01' AND '2013-01-01'
            ORDER BY start_time ASC LIMIT 1
        ) AND
        crawl_id < (
            SELECT id FROM main_crawl
            WHERE start_time BETWEEN '2012-01-01' AND '2013-01-01'
            ORDER BY start_time DESC LIMIT 1
        )
    group by crawl_id, group_id having count(*) > 1
) as asd;

-- Counts crawls with duplicate hitgroupsstatuses
select count(distinct crawl_id) as to_fix from (
    select crawl_id
    from main_hitgroupstatus
    group by crawl_id, group_id
    having count(*) > 1
) as asd;

-- Investigating db_arrivals agregations
SELECT crawl_id, group_id, hits_consumed, hits_posted, hits_available
FROM hits_mv
WHERE
    (hits_posted IS NOT NULL OR hits_consumed IS NOT NULL) AND
    start_time BETWEEN '2012-08-01' AND '2012-08-02'
ORDER BY group_id, crawl_id ASC;

-- Hitgroupstatus count
select count(*) FROM main_hitgroupstatus
WHERE crawl_id >= (
    SELECT min(id) FROM main_crawl
    WHERE start_time > '2012-01-01'
) AND
crawl_id <= (
    SELECT max(id) FROM main_crawl
    WHERE start_time < '2013-01-01'
);
--   count
-- ----------
--  90763030
-- (1 row)
-- Time: 1167808.061 ms

import datetime
from django.utils.timezone import now
import time
today = now().date()
dates = [today - datetime.timedelta(days=x) for x in range(0, 200)]
for i, dt in enumerate(dates, start=1):
    tt = time.time()
    print sum([
        sum([
            crawl.hitgroupstatus_set.get(hit_group_content__id=content.id
            ).hits_available for content in  crawl.hitgroupcontent_set.all()
        ]) for crawl in
            Crawl.objects.filter(
                start_time__gt=dt, start_time__lt=dt + datetime.timedelta(days=1))
    ])
    print '{0}. {1} {2} elapsed'.format(i, dt, time.time() - tt)

select count(is_spam=true) from hits_mv where start_time between '2012-08-01' and '2012-08-02' group by crawl_id;
