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
-- Exporting query to a csv.
--
echo "COPY (<query_goes_here>) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/<report_name>.csv' -d mturk_tracker_db -U mturk_tracker

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
-- The following lines will output .csv files to /tmp/mtracker_reports/crawlagregates_arrivals_*.csv.
--
echo "COPY (SELECT date_trunc('day', start_time) as unit, count(*) as total, round(CAST (avg(hits_posted) as NUMERIC), 2) as hits_posted, round(CAST (avg(hits_consumed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(rewards_posted) as NUMERIC), 2) as rewards_posted, round(CAST (avg(rewards_consumed) as NUMERIC), 2) as rewards_consumed FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/crawlagregates_arrivals_day.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('week', start_time) as unit, count(*) as total, round(CAST (avg(hits_posted) as NUMERIC), 2) as hits_posted, round(CAST (avg(hits_consumed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(rewards_posted) as NUMERIC), 2) as rewards_posted, round(CAST (avg(rewards_consumed) as NUMERIC), 2) as rewards_consumed FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/crawlagregates_arrivals_week.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('month', start_time) as unit, count(*) as total, round(CAST (avg(hits_posted) as NUMERIC), 2) as hits_posted, round(CAST (avg(hits_consumed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(rewards_posted) as NUMERIC), 2) as rewards_posted, round(CAST (avg(rewards_consumed) as NUMERIC), 2) as rewards_consumed FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/crawlagregates_arrivals_month.csv' -d mturk_tracker_db -U mturk_tracker

--
-- AVERAGE CRAWLAGGREGATE DATA
--
-- (count, hits, projects, reward) for day/week/month
--
SELECT
    date_trunc('day', start_time) as unit,
    count(*) as total,
    round(CAST (avg(hits) as NUMERIC), 2) as hits,
    round(CAST (avg(projects) as NUMERIC), 2) as projects,
    round(CAST (avg(reward) as NUMERIC), 2) as reward
FROM
    main_crawlagregates
GROUP BY unit
ORDER BY unit DESC
--
-- The following lines will output .csv files to /tmp/mtracker_reports/crawlagregates_*.csv.
--
echo "COPY (SELECT date_trunc('day', start_time) as unit, count(*) as total, round(CAST (avg(hits) as NUMERIC), 2) as hits, round(CAST (avg(projects) as NUMERIC), 2) as projects, round(CAST (avg(reward) as NUMERIC), 2) as reward FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/crawlagregates_day.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('week', start_time) as unit, count(*) as total, round(CAST (avg(hits) as NUMERIC), 2) as hits, round(CAST (avg(projects) as NUMERIC), 2) as projects, round(CAST (avg(reward) as NUMERIC), 2) as reward FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/crawlagregates_week.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('month', start_time) as unit, count(*) as total, round(CAST (avg(hits) as NUMERIC), 2) as hits, round(CAST (avg(projects) as NUMERIC), 2) as projects, round(CAST (avg(reward) as NUMERIC), 2) as reward FROM main_crawlagregates GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/crawlagregates_month.csv' -d mturk_tracker_db -U mturk_tracker

--
-- AVERAGE DAYILY STATS DATA
--
-- Average arrivals data for day, week and month.
--
SELECT
    date_trunc('month', date) as unit,
    count(*) as total,
    round(CAST (avg(arrivals) as NUMERIC), 2) as hits_posted,
    round(CAST (avg(arrivals_value) as NUMERIC), 2) as rewards_posted,
    round(CAST (avg(processed) as NUMERIC), 2) as hits_consumed,
    round(CAST (avg(processed_value) as NUMERIC), 2) as rewards_consumed
FROM
    main_daystats
GROUP BY unit
ORDER BY unit DESC
--
-- The following lines will output .csv files to /tmp/mtracker_reports/daystats_*.csv.
--
echo "COPY (SELECT date_trunc('day', date) as unit, count(*) as total, round(CAST (avg(arrivals) as NUMERIC), 2) as hits_posted, round(CAST (avg(arrivals_value) as NUMERIC), 2) as rewards_posted, round(CAST (avg(processed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(processed_value) as NUMERIC), 2) as rewards_consumed FROM main_daystats GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/daystats_day.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('week', date) as unit, count(*) as total, round(CAST (avg(arrivals) as NUMERIC), 2) as hits_posted, round(CAST (avg(arrivals_value) as NUMERIC), 2) as rewards_posted, round(CAST (avg(processed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(processed_value) as NUMERIC), 2) as rewards_consumed FROM main_daystats GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/daystats_week.csv' -d mturk_tracker_db -U mturk_tracker
echo "COPY (SELECT date_trunc('month', date) as unit, count(*) as total, round(CAST (avg(arrivals) as NUMERIC), 2) as hits_posted, round(CAST (avg(arrivals_value) as NUMERIC), 2) as rewards_posted, round(CAST (avg(processed) as NUMERIC), 2) as hits_consumed, round(CAST (avg(processed_value) as NUMERIC), 2) as rewards_consumed FROM main_daystats GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/daystats_month.csv' -d mturk_tracker_db -U mturk_tracker


--
-- INVESTIGATING PEAK IN CRAWLS (for date 2012-02-01 to 2012-04-01)
--
SELECT hgc.requester_name, *
FROM (
    SELECT requester_id,
        count(DISTINCT group_id) as groups,
        sum(hits_posted) as hits_posted,
        sum(hits_consumed) as hits_consumed,
        avg(hits_available) as hits_available
    FROM
        hits_mv
    WHERE
        start_time BETWEEN '2012-02-22' AND '2012-02-23'
    GROUP BY
        requester_id
) asd
LEFT JOIN
    main_hitgroupcontent hgc
ON asd.requester_id = hgc.requester_id


SELECT requester_id, count(DISTINCT group_id) as groups, sum(hits_posted) as hits_posted, sum(hits_consumed) as hits_consumed, avg(hits_available) as hits_available FROM hits_mv WHERE start_time BETWEEN '2012-02-22' AND '2012-02-23' GROUP BY requester_id ORDER BY hits_available
echo "COPY (SELECT requester_id, count(DISTINCT group_id) as groups, sum(hits_posted) as hits_posted, sum(hits_consumed) as hits_consumed, avg(hits_available) as hits_available FROM hits_mv WHERE start_time BETWEEN '2012-03-05' AND '2012-03-10' GROUP BY requester_id ORDER BY hits_available) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/02-22--23-topreq.csv' -d mturk_tracker_db -U mturk_tracker

--
-- requester name
--
select distinct(requester_name) from main_hitgroupcontent where requester_id IN ('A2V6GCHMZ3W89V', 'A2SUM2D7EOAK1T', 'A2EDWXB05RXJRZ', 'A32TTE4XXN6MQZ',' AALZYJEWCVBZB', 'A2IR7ETVOIULZU', 'A2TXMKDL52OV8E', 'A1MPL3YJI1LE8G',' AEU3H8GUL27PE', 'A1ZD2GJV95O4BV', 'A24UU3V85ET09I',' A1X3YGKV0J0C2', 'A3K54QYGJEOX5Q', 'A2NQZ00KZ19EOA',' ALMQ6VRHL56SY', 'A31SSWVOPS02XL', 'A2YW2GCVA51U3S', 'A1CTI3ZAWTR5AZ',' A8KS2AK5LE3YO', 'A3MI6MIUNWCR7F',' A85UAWGX7A330', 'A1XZO7BXDYY98N', 'A1C7A4QXPNC94C', 'A2CQVSX8OBR5X1', 'AC8EP1ITDMJPH');
select requester_name from main_hitgroupcontent where requester_id='A32TTE4XXN6MQZ' LIMIT 1;

--
-- hits posted for specific requester
--
SELECT
    date_trunc('month', start_time) as unit,
    count(distinct group_id) as groups,
    sum(hits_posted) as hits_posted,
    sum(hits_consumed) as hits_consumed,
    avg(hits_available) as hits_available
FROM
    hits_mv
WHERE
    requester_id = 'A32TTE4XXN6MQZ'
GROUP BY unit
ORDER BY unit DESC

echo "COPY (SELECT date_trunc('month', start_time) as unit, count(*) as groups, sum(hits_posted) as hits_posted, sum(hits_consumed) as hits_consumed, avg(hits_available) as hits_available FROM hits_mv WHERE requester_id = 'A32TTE4XXN6MQZ'GROUP BY unit ORDER BY unit DESC) TO STDOUT WITH CSV HEADER" | psql -o '/tmp/mtracker_reports/req_A32TTE4XXN6MQZ_in_time.csv' -d mturk_tracker_db -U mturk_tracker
