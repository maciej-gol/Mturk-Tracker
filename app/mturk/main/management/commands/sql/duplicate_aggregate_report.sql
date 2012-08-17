CREATE OR REPLACE FUNCTION count_extra(
    istart TIMESTAMP WITH TIME ZONE, iend TIMESTAMP WITH TIME ZONE)
        RETURNS VOID AS '
    DECLARE
        total_hmv integer; corrected_hmv integer;
        removed_hmv integer; extra_avg_hmv float;
        hmv_row RECORD;
        total_hgs integer; corrected_hgs integer;
        removed_hgs integer; extra_avg_hgs float;
        hgs_row RECORD;
    BEGIN
        RAISE NOTICE ''Counting multiplied records in main_hitgroupstatus
        and hits_mv tables.'';
        RAISE NOTICE ''Interval: % to %'', istart, iend;
        SELECT count(*)
        INTO total_hgs
        FROM main_hitgroupstatus
        WHERE crawl_id > (
                    SELECT min(id) FROM main_crawl
                    WHERE start_time BETWEEN istart AND iend
                ) AND
                crawl_id < (
                    SELECT max(id) FROM main_crawl
                    WHERE start_time BETWEEN istart AND iend
                );

        SELECT INTO
            corrected_hgs, removed_hgs, extra_avg_hgs *
        FROM (
            SELECT count(*), sum(asd.extra - 1), avg(asd.extra - 1)
            FROM (
                SELECT group_id, crawl_id, count(*) AS extra
                FROM main_hitgroupstatus
                WHERE
                    crawl_id > (
                        SELECT min(id) FROM main_crawl
                        WHERE start_time BETWEEN istart AND iend
                    ) AND
                    crawl_id < (
                        SELECT max(id) FROM main_crawl
                        WHERE start_time BETWEEN istart AND iend
                    )
                GROUP BY crawl_id, group_id
                HAVING count(*) > 1
            ) as asd
        ) as zxc;

        RAISE NOTICE ''main_hitgroupstatus table'';
        RAISE NOTICE ''Total:      %'', total_hgs;
        RAISE NOTICE ''Correct:    %'', total_hgs - removed_hgs;
        RAISE NOTICE ''To correct:  %'', corrected_hgs;
        RAISE NOTICE ''To remove:   %'', removed_hgs;
        RAISE NOTICE ''Extra avg:  %'', extra_avg_hgs;

        SELECT count(*)
        INTO total_hmv
        FROM hits_mv
        WHERE crawl_id > (
                    SELECT min(id) FROM main_crawl
                    WHERE start_time BETWEEN istart AND iend
                ) AND
                crawl_id < (
                    SELECT max(id) FROM main_crawl
                    WHERE start_time BETWEEN istart AND iend
                );

        SELECT INTO
            corrected_hmv, removed_hmv, extra_avg_hmv *
        FROM (
            SELECT count(*), sum(asd.extra - 1), avg(asd.extra - 1)
            FROM (
                SELECT group_id, crawl_id, count(*) AS extra
                FROM hits_mv
                WHERE
                    crawl_id > (
                        SELECT min(id) FROM main_crawl
                        WHERE start_time BETWEEN istart AND iend
                    ) AND
                    crawl_id < (
                        SELECT max(id) FROM main_crawl
                        WHERE start_time BETWEEN istart AND iend
                    )
                GROUP BY crawl_id, group_id
                HAVING count(*) > 1
            ) as asd
        ) as zxc;

        RAISE NOTICE ''hits_mv table'';
        RAISE NOTICE ''Total:      %'', total_hmv;
        RAISE NOTICE ''Correct:    %'', total_hmv - removed_hmv;
        RAISE NOTICE ''To correct: %'', corrected_hmv;
        RAISE NOTICE ''To remove:  %'', removed_hmv;
        RAISE NOTICE ''Extra avg:  %'', extra_avg_hmv;

    END;
'
LANGUAGE plpgsql;
