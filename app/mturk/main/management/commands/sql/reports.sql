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
