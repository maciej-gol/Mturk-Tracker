declare
  minimum integer;
  maximum integer;
  i integer; hits integer; grp integer; grp1 integer; grp2 integer;
  prj_started integer; prj_completed integer;

begin
  select max(id) into i from main_crawl;

  /* Selects hits_available difference (aka. hits_diff) for grouped by group_id
   * for two most recent crawls.
  */
  select (coalesce(a.hits_available, 0) - coalesce(b.hits_available, 0)),
    a.group_id, b.group_id into hits, grp1, grp2
    from ((select group_id, hits_available from main_hitgroupstatus
             where crawl_id = i) a
           full outer join
             (select group_id, hits_available from main_hitgroupstatus
              where crawl_id = i - 1) b
           on a.group_id = b.group_id);

  /* Finds the count of hitgroups started between the crawls. */
  select count(1) into prj_started from (
    (select group_id from main_hitgroupstatus where crawl_id=i) a
    full outer join
    (select group_id from main_hitgroupstatus where crawl_id=i - 1) b
    on a.group_id=b.group_id) where b.group1 is null;

  /* Finds the count of hitgroups completed between the crawls. */
  select count(1) into prj_completed from (
    (select group_id from main_hitgroupstatus where crawl_id=i) a
    full outer join
    (select group_id from main_hitgroupstatus where crawl_id=i - 1) b
    on a.group_id=b.group_id) where a.group1 is null;

  /* Saves the above as projects_arrived and projects_completed into
   * main_hitgroupstatus.
  */
  update main_hitgroupstatus set projects_arrived = prj_started
    where crawl_id=i;
  update main_hitgroupstatus set projects_completed = prj_started
    where crawl_id=i;

  /* Saves hits_arrived or hits_consumed. */
  if(hits >= 0)
  then
    update main_hitgroupstatus set hits_arrived=hits
      where group_id=grp1 and crawl_id=i;
  else
    update main_hitgroupstatus set hits_consumed=hits
      where group_id=grp2 and crawl_id=i - 1;
  end if;
END;
