declare
  minimum integer;
  maximum integer;
  i integer; hits integer; grp1 varchar(50); grp2 varchar(50);
  prj_started integer; prj_completed integer;
begin
  /* Selects crawls for last week, excluding today. */
  select max(id) into maximum from main_crawl
    where date(start_time) = date(current_timestamp) - 1;
  select min(id) into minimum from main_crawl
    where date(start_time) = date(current_timestamp) - 8;

  RAISE NOTICE 'Positive id % % ', minimum, maximum;
  FOR i in (select id from main_crawl where id between minimum and maximum) LOOP
    /* Inserts (hits_diff, group_id, group_id, crawl_id, crawl_id - 1) into
     * hits_temp.
    */
    insert into hits_temp(
      select (coalesce(a.hits_available, 0) - coalesce(b.hits_available, 0)),
        a.group_id, b.group_id, i, i - 1 from (
          (select group_id, hits_available from main_hitgroupstatus
            where crawl_id = i) a
          full outer join
          (select group_id, hits_available from main_hitgroupstatus
            where crawl_id = i - 1) b
          on a.group_id = b.group_id));

    /* Finds the count of hitgroups started between the crawls. */
    select count(1) into prj_started from (
      (select group_id from main_hitgroupstatus where crawl_id=i) a
      full outer join
      (select group_id from main_hitgroupstatus where crawl_id=i - 1) b
      on a.group_id=b.group_id) where b.group_id is null;

    /* Finds the count of hitgroups completed between the crawls. */
    select count(1) into prj_completed from (
      (select group_id from main_hitgroupstatus where crawl_id=i) a
      full outer join
      (select group_id from main_hitgroupstatus where crawl_id=i-1) b
      on a.group_id=b.group_id) where a.group_id is null;

    /* Updates crawlagregates. */
    update main_crawlagregates set hitsgroups_posted = prj_started where id=i;
    update main_crawlagregates set hitsgroups_consumed = prj_completed where id=i;
  END LOOP;
END;
