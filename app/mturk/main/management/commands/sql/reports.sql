--
-- MISC DATA REPORTS
--

--
-- CORRECT CRAWLS
--
-- Presents the numbers of incorrect/correct crawls in a month, where
-- correctness is defined by: groups_available * 0.9 < groups_downloaded and
-- having groups_available.
--
-- │         month          | total | correct | incorrect | correct_ratio
-- │------------------------+-------+---------+-----------+---------------
--
SELECT *, total - correct as incorrect, 100 * correct / total as correct_percent
FROM (
    SELECT date_trunc('month', start_time) as "month",
        count(*) as total,
        count(CASE WHEN groups_available * 0.9 < groups_downloaded
            THEN true ELSE NULL END) as correct
    FROM main_crawl
    GROUP BY month
    ORDER BY month DESC
) asd;

--
-- AVERAGE ARRIVALS DATA
--
-- Average arrivals data for day, week and month.
--
SELECT
    date_trunc('day', start_time) as unit,
    count(*) as total,
    round(CAST (avg(hits_posted) as NUMERIC), 2) as hits_posted,
    round(CAST (avg(hits_consumed) as NUMERIC), 2) as hits_consumed,
    round(CAST (avg(rewards_posted) as NUMERIC), 2) as rewards_posted,
    round(CAST (avg(rewards_consumed) as NUMERIC), 2) as rewards_consumed
FROM
    main_crawlagregates
GROUP BY unit
ORDER BY unit DESC
--
-- The following lines will output .csv files to /tmp/mtracker_reports/.
--
echo "COPY (SELECT date_trunc('day', start_time) as unit, count(*) as total, round(CAST (avg(hits_posted) as NUMERIC), 2) as hits_posted, round(CAST (avg(hits_consumed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(rewards_posted) as NUMERIC), 2) as rewards_posted, round(CAST (avg(rewards_consumed) as NUMERIC), 2) as rewards_consumed FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/day.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('week', start_time) as unit, count(*) as total, round(CAST (avg(hits_posted) as NUMERIC), 2) as hits_posted, round(CAST (avg(hits_consumed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(rewards_posted) as NUMERIC), 2) as rewards_posted, round(CAST (avg(rewards_consumed) as NUMERIC), 2) as rewards_consumed FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/week.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('month', start_time) as unit, count(*) as total, round(CAST (avg(hits_posted) as NUMERIC), 2) as hits_posted, round(CAST (avg(hits_consumed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(rewards_posted) as NUMERIC), 2) as rewards_posted, round(CAST (avg(rewards_consumed) as NUMERIC), 2) as rewards_consumed FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/month.csv' -d mturk_tracker_db -U mturk_tracker
