declare
  minimum integer;
  maximum integer;
  lag_id integer; cur_id integer;
  hits integer; grp1 varchar(50); grp2 varchar(50);
  prj_started integer; prj_completed integer;

begin

  RAISE NOTICE 'Processing crawls from % to % ', istart, iend;

  FOR lag_id, cur_id in (
    select (lag(id, 1, null) over (order by start_time desc)), id
     from main_crawl
      where
        istart <= start_time and start_time <= iend and
        groups_available * 0.9 < groups_downloaded
      order by start_time desc)
  LOOP
    RAISE NOTICE 'lag_id % cur_id % ', lag_id, cur_id;
    IF(lag_id <> null AND cur_id <> null AND lag_id <> cur_id) THEN
      /* Inserts (hits_diff, group_id, group_id, crawl_id, crawl_id - 1) into
       * hits_temp.
       *
       * We are saving both group_ids later to find crawls where the group
       * appeared (first group_id is null) or
       * disappeared (second group_id is null)
      */
      insert into hits_temp(
        select (coalesce(a.hits_available, 0) - coalesce(b.hits_available, 0)),
          a.group_id, b.group_id, cur_id, lag_id from (
            (select group_id, hits_available from main_hitgroupstatus
              where crawl_id = cur_id) a
            full outer join
            (select group_id, hits_available from main_hitgroupstatus
              where crawl_id = lag_id) b
            on a.group_id = b.group_id));

      /* Finds the count of hitgroups started between the crawls. */
      select count(1) into prj_started from (
        (select group_id from main_hitgroupstatus where crawl_id=cur_id) a
        full outer join
        (select group_id from main_hitgroupstatus where crawl_id=lag_id) b
        on a.group_id=b.group_id) where b.group_id is null;

      /* Finds the count of hitgroups completed between the crawls. */
      select count(1) into prj_completed from (
        (select group_id from main_hitgroupstatus where crawl_id=cur_id) a
        full outer join
        (select group_id from main_hitgroupstatus where crawl_id=lag_id) b
        on a.group_id=b.group_id) where a.group_id is null;

      /* Updates crawlagregates. */
      update main_crawlagregates
        set hitgroups_posted = prj_started,  hitgroups_consumed = prj_completed
        where crawl_id=cur_id;
    END IF;

    if(cur_id % 100 = 0) then
      RAISE NOTICE 'Positive id % ', cur_id;
    end if;

  END LOOP;
END;
