declare
  minimum integer;
  maximum integer;
  i integer; crawl integer; grp1 varchar(50); grp2 varchar(50);
  total_reward_consumed float; prj_completed integer; total_reward_posted float;

begin
  /* Select records for past week. */
  select max(id) into maximum from main_crawl
    where date(start_time) = date(current_timestamp) - 1;
  select min(id) into minimum from main_crawl
    where date(start_time) = date(current_timestamp) - 8;

  RAISE NOTICE 'Positive id % % ', minimum, maximum;
  FOR i in (select id from main_crawl where id between minimum and maximum) LOOP

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

    if((i - minimum) % 1000 = 0) then
      RAISE NOTICE 'Positive id % ', i;
    end if;

  END LOOP;
END;

