--
-- Hits mv
--

CREATE INDEX groupid_crawlid_hitsposted ON hits_mv USING btree (group_id, crawl_id, hits_posted);
CREATE INDEX groupid_crawlid_hitsconsumed ON hits_mv USING btree (group_id, crawl_id, hits_consumed);


--
-- Main crawlagregates
--

CREATE INDEX crawlid_rewardsconsumed ON main_crawlagregates USING btree (crawl_id, rewards_posted);
CREATE INDEX crawlid_rewardsposted ON main_crawlagregates USING btree (crawl_id, rewards_consumed);
