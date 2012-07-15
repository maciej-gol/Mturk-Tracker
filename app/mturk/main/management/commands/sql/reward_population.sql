declare
  i integer; crawl integer;
  total_reward_consumed float; total_reward_posted float;

BEGIN

  RAISE NOTICE 'Processing crawls from % to %.', istart, iend;
  FOR i IN (SELECT id FROM main_crawl
            WHERE start_time BETWEEN istart AND iend)
  LOOP
    /* Calculate the total reward consumed from hits_mv. */
    select crawl_id, sum(coalesce(hits_consumed, 0) * reward)
      into crawl, total_reward_consumed from hits_mv
      where crawl_id = i group by crawl_id;

    /* Calculate the total reward posted from hits_mv. */
    select crawl_id, sum(coalesce(hits_posted, 0) * reward)
      into crawl, total_reward_posted from hits_mv
      where crawl_id = i group by crawl_id;

    /* The data to the main_crawlaggredates. */
    update main_crawlagregates
      set rewards_consumed = total_reward_consumed,
          rewards_posted = total_reward_posted
      where crawl_id = i;

    if (i % 1000 = 0) then
      RAISE NOTICE 'Processing crawl % ', i;
    end if;

  END LOOP;
END;

