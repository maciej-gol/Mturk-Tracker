declare
i integer;

CUR1 CURSOR FOR SELECT * FROM hits_temp;

  -- We are deleting hits_temp after each iteration anyway, no need to add extra
  -- constaints on this select.

  -- WHERE crawl_id IN (
  --   SELECT id FROM main_crawl
  --   WHERE start_time BETWEEN istart AND iend) AND
  --   groups_available * 0.9 < groups_downloaded;

begin
  RAISE NOTICE 'Processing crawls from % to %.', istart, iend;
  i :=1;

  FOR REC IN CUR1
  LOOP

    -- Sets both hits_posted and hits_consumed to 0.

    -- The below updates are extra-slow, they are not required with fresh data
    -- and can be ran manually when re-calculating results.

    -- update hits_mv
    --   set hits_posted = 0
    --   where group_id = REC.group_id1 and crawl_id = REC.crawl_id;
    -- update hits_mv
    --   set hits_consumed = 0
    --   where group_id = REC.group_id2 and crawl_id = REC.prev_crawl_id;

    -- Sets hits_posted or hits_consumed.
    -- Hits temp is: (hits_diff, group_id, group_id, crawl_id, crawl_id - 1)
    if(REC.hits >= 0) then
      update hits_mv
        set hits_posted = REC.hits
        where group_id = REC.group_id1 and crawl_id = REC.crawl_id
        and hits_available != REC.hits;
    else
      update hits_mv
        set hits_consumed = (-1) * REC.hits
        -- Settings prev_crawl_id here is important, makes finding cases where
        -- hits_avaialble equals hits_consumed possible.
        where group_id = REC.group_id2 and crawl_id = REC.prev_crawl_id
        and hits_available != (-1) * REC.hits;
    end if;

    if(i % 1000 = 0) then
      RAISE NOTICE 'Processing crawl % ', i;
    end if;

    i := i+1;
  END LOOP;

  RAISE NOTICE 'Delecting all hits_temp records (from % to %).', istart, iend;

  -- ONLY one instance can run at a time, but truncate will be faster than
  -- delete in this case, as we can except 15k+ records

  TRUNCATE hits_temp;

  -- DELETE FROM hits_temp
  --   WHERE crawl_id IN (
  --     SELECT id FROM main_crawl
  --     WHERE start_time BETWEEN istart AND iend
  --   );

  RAISE NOTICE 'Finishing.';
END;
