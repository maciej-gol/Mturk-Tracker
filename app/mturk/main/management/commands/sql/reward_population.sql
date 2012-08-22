declare
  i integer;
  total_hits_posted integer; total_hits_consumed integer;
  total_reward_consumed float; total_reward_posted float;

BEGIN

  RAISE NOTICE 'Processing crawls from % to %.', istart, iend;
  FOR i IN (SELECT id FROM main_crawl
            WHERE start_time BETWEEN istart AND iend)
  LOOP

    /* Calculate the total reward consumed/posted from hits_mv. */
    SELECT
      sum(coalesce(hits_consumed, 0)),
      sum(coalesce(hits_posted, 0)),
      sum(coalesce(hits_consumed, 0) * reward),
      sum(coalesce(hits_posted, 0) * reward)
    INTO
      total_hits_consumed, total_hits_posted,
      total_reward_consumed, total_reward_posted
    FROM hits_mv
    WHERE crawl_id = i;

    /* The data to the main_crawlaggredates. */
    UPDATE main_crawlagregates
    SET
      hits_posted = total_hits_posted,
      hits_consumed = total_hits_consumed,
      rewards_consumed = total_reward_consumed,
      rewards_posted = total_reward_posted
    WHERE crawl_id = i;

    if (i % 1000 = 0) then
      RAISE NOTICE 'Processing crawl % ', i;
    end if;

  END LOOP;
END;
