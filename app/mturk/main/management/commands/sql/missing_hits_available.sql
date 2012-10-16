--
-- REPORTS AND FIXERS TO MISSING GROUPS_AVAILABLE PROBLEM
--
-- The problem was greatest for records before mid 2010-07-01 when
-- groups_available was simply not set on the records. It was solved by copying
-- groups_downloaded to groups_avaialable for that period.
--
-- Any crawls past that date, that did not have the groups_available information
-- must have been unable to download the information from mturk.com, which until
-- recently (2012-10-15) was downloaded without any retries.
--
-- Reports are useful for statistics and error reporting and they are left in
-- here.
--

--
-- CRAWLS WITH MISSING GROUPS_AVAILABLE
--
-- Produces a table:
--
--          month          | total | missing | available
-- ------------------------+-------+---------+-----------
--
-- The numbers are counts of crawls for a given year, month that have or don't
-- have groups_available set. Used for checking duplicate_aggregates_report and
-- detecting months that may still have some duplicates to remove.
--
SELECT *, total - available as missing
FROM (
    SELECT date_trunc('month', start_time) as "month",
        count(*) as total,
        count(groups_available) as available
    FROM main_crawl
    GROUP BY month
    ORDER BY month DESC
) asd;


--
-- HITGROUPSTATUSES WITH MISSING GROUPS_AVAILABLE
--
-- As above, but for related main_hitgroupstatus
--
SELECT *, total - available
FROM (
    SELECT date_trunc('month', mc.start_time) as "month",
        count(*) as total,
        count(mc.groups_available) as available
    FROM main_crawl mc
    JOIN main_hitgroupstatus hgs
    ON mc.id = hgs.crawl_id
    GROUP BY month
    ORDER BY month DESC
) asd;

--
-- FIXING MISSING GROUPS_AVAILABLE
--
-- As mentioned before, crawls before 2010-08-01 had groups_available copied
-- from groups_downloaded. It may appear, the crawls downloaded all available
-- groups, which is obviously not true.
--
-- Make sure NOT to run this on records past 2010-08-01!!!
--
UPDATE main_crawl
SET groups_available = groups_downloaded
WHERE start_time <= '2010-08-01' AND groups_available IS NULL;
