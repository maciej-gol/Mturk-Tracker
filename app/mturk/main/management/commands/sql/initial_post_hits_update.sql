-- This procedure updates hits_mv records related to initial post of a group.

-- Such recods would have hits_posted = hits_available and thus be ignored by
-- hits_update function because of the invalid hit posting filter. Therefore
-- the data has to be updated in a separate function.

-- The procedure will search for hitgroupcontents with first_crawl in the given
-- interval and update matching hits_mv entries.

BEGIN

  RAISE NOTICE 'Processing crawls from % to %.', istart, iend;

  UPDATE hits_mv
    SET hits_posted = group_first_post.hits_available
    FROM (
      SELECT status.group_id, status.crawl_id, status.hits_available
      FROM
        (
          SELECT group_id, first_crawl_id
          FROM main_hitgroupcontent
          WHERE first_crawl_id IN (
            SELECT id FROM main_crawl
            WHERE start_time BETWEEN istart AND iend
          )
        ) as content
        LEFT JOIN
        (
          SELECT group_id, crawl_id, hits_available
          FROM main_hitgroupstatus
          WHERE crawl_id IN (
            SELECT id FROM main_crawl
            WHERE start_time BETWEEN istart AND iend
          )
        ) as status
        ON
          content.group_id = status.group_id AND
          content.first_crawl_id = status.crawl_id
  ) as group_first_post
  WHERE
    hits_mv.group_id = group_first_post.group_id AND
    hits_mv.crawl_id = group_first_post.crawl_id;

END;
