declare
  minimum integer;
  maximum integer;
  i integer; hits integer; grp1 varchar(50); grp2 varchar(50);
  prj_started integer; prj_completed integer;

begin
  select max(id) into maximum from main_crawl
    where date(start_time) = date(current_timestamp);

  select min(id) into minimum from main_crawl
    where date(start_time) = date(current_timestamp) - 1;

  RAISE NOTICE 'Positive id % % ', minimum, maximum;
  FOR i in (select id from main_crawl where id between minimum and maximum) LOOP
    select (coalesce(a.hits_available, 0) - coalesce(b.hits_available, 0)),
      a.group_id, b.group_id
      into hits, grp1, grp2
      from
        ((select group_id, hits_available from main_hitgroupstatus
          where crawl_id = i) a
      full outer join
        (select group_id, hits_available from main_hitgroupstatus
          where crawl_id = i - 1) b
      on a.group_id = b.group_id);

    /* TODO: Missing the update part ? */

  END LOOP;
END;

